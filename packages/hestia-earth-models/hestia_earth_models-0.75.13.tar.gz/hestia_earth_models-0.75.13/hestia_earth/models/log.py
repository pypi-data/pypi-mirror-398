from enum import Enum
from functools import reduce
import os
import sys
import logging
from typing import Callable, List, Optional, Union
from numpy.typing import NDArray
from numpy import ndarray

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
_EXTENDED_LOGS = os.getenv("LOG_EXTENDED", "true") == "true"
_LOG_DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%dT%H:%M:%S%z")

# disable root logger
root_logger = logging.getLogger()
root_logger.disabled = True

# create custom logger
logger = logging.getLogger("hestia_earth.models")
logger.removeHandler(sys.stdout)
logger.setLevel(logging.getLevelName(LOG_LEVEL))


def log_to_file(filepath: str):
    """
    By default, all logs are saved into a file with path stored in the env variable `LOG_FILENAME`.
    If you do not set the environment variable `LOG_FILENAME`, you can use this function with the file path.

    Parameters
    ----------
    filepath : str
        Path of the file.
    """
    formatter = (
        logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            _LOG_DATE_FORMAT,
        )
        if _EXTENDED_LOGS
        else logging.Formatter(
            '{"logger": "%(name)s", "message": "%(message)s"}', _LOG_DATE_FORMAT
        )
    )
    handler = logging.FileHandler(filepath, encoding="utf-8")
    handler.setFormatter(formatter)
    handler.setLevel(logging.getLevelName(LOG_LEVEL))
    logger.addHandler(handler)


LOG_FILENAME = os.getenv("LOG_FILENAME")
if LOG_FILENAME is not None:
    log_to_file(LOG_FILENAME)


def _join_args(**kwargs):
    return ", ".join([f"{key}={value}" for key, value in kwargs.items()])


def _log_node_suffix(node: dict):
    node_type = node.get("@type", node.get("type"))
    node_id = node.get("@id", node.get("id", node.get("term", {}).get("@id")))
    return f"{node_type.lower()}={node_id}, " if node_type else ""


def debugValues(log_node: dict, **kwargs):
    logger.debug(_log_node_suffix(log_node) + _join_args(**kwargs))


def logRequirements(log_node: dict, **kwargs):
    logger.info(
        _log_node_suffix(log_node) + "requirements=true, " + _join_args(**kwargs)
    )


def logShouldRun(
    log_node: dict, model: str, term: Union[str, None], should_run: bool, **kwargs
):
    extra = (", " + _join_args(**kwargs)) if len(kwargs.keys()) > 0 else ""
    logger.info(
        _log_node_suffix(log_node) + "should_run=%s, model=%s, term=%s" + extra,
        should_run,
        model,
        term,
    )


def debugMissingLookup(
    lookup_name: str, row: str, row_value: str, col: str, value, **kwargs
):
    if value is None or value == "":
        extra = (", " + _join_args(**kwargs)) if len(kwargs.keys()) > 0 else ""
        logger.warning(
            f"Missing lookup={lookup_name}, {row}={row_value}, column={col}" + extra
        )


def logErrorRun(model: str, term: str, error: str):
    logger.error("model=%s, term=%s, error=%s", model, term, error)


def log_as_table(values: Union[list, dict], ignore_keys: list = []):
    """
    Log a list of values to display as a table.
    Can either use a single dictionary, represented using id/value pair,
    or a list of dictionaries using their keys as columns.

    Parameters
    ----------
    values : list | dict
        Values to display as a table.
    """
    return (
        ";".join(
            [f"id:{k}_value:{v}" for k, v in values.items() if k not in ignore_keys]
            if isinstance(values, dict)
            else [
                (
                    "_".join(
                        [f"{k}:{v}" for k, v in value.items() if k not in ignore_keys]
                    )
                    if isinstance(value, dict)
                    else str(value)
                )
                for value in values
            ]
        )
        or "None"
    )


def log_blank_nodes_id(blank_nodes: List[dict]):
    """
    Log a list of blank node ids to display as a table.

    Parameters
    ----------
    values : list
        List of blank nodes, like Product, Input, Measurement, etc.
    """
    return (
        ";".join(
            [
                p.get("term", {}).get("@id")
                for p in blank_nodes
                if p.get("term", {}).get("@id")
            ]
        )
        or "None"
    )


_INVALID_CHARS = {"_", ":", ",", "="}
_REPLACEMENT_CHAR = "-"


def format_str(value: Optional[str], default: str = "None") -> str:
    """Format a string for logging in a table. Remove all characters used to render the table on the front end."""
    return (
        reduce(
            lambda x, char: x.replace(char, _REPLACEMENT_CHAR),
            _INVALID_CHARS,
            str(value),
        )
        if value
        else default
    )


def format_bool(value: Optional[bool], default: str = "None") -> str:
    return str(value) if isinstance(value, bool) else default


def format_float(
    value: Union[int, float, None],
    unit: str = "",
    default: str = "None",
    ndigits: int = 3,
) -> str:
    return (
        " ".join(
            string
            for string in [f"{round(value, ndigits)}", format_str(unit, "")]
            if string
        )
        if isinstance(value, (float, int))
        else default
    )


def format_int(
    value: Union[int, float, None], unit: str = "", default: str = "None"
) -> str:
    return format_float(value, unit=unit, default=default, ndigits=None)


def _format_nd_array(
    value: Optional[NDArray], unit: str = "", default: str = "None", ndigits: int = 3
) -> str:
    return (
        " ".join(
            string
            for string in [
                f"{format_float(value.mean(), ndigits=ndigits)} ± {format_float(value.std(), ndigits=ndigits)}",
                format_str(unit, ""),
            ]
            if string
        )
        if isinstance(value, ndarray)
        else default
    )


TYPE_TO_FORMAT_FUNC = {ndarray: _format_nd_array, (float, int): format_float}


def format_nd_array(
    value: Optional[NDArray], unit: str = "", default: str = "None", ndigits: int = 3
) -> str:
    """
    Format a numpy array for logging in a table.

    Values that are floats and ints are logged using `format_float`.
    """
    format_func = next(
        (
            func
            for type_, func in TYPE_TO_FORMAT_FUNC.items()
            if isinstance(value, type_)
        ),
        None,
    )
    return (
        format_func(value, unit=unit, default=default, ndigits=ndigits)
        if format_func
        else default
    )


def format_decimal_percentage(
    value: Optional[float], unit: str = "pct", default: str = "None", ndigits: int = 3
) -> str:
    """Format a decimal percentage (0-1) as a percentage (0-100%) for logging in a table."""
    return (
        format_float(value * 100, unit=unit, ndigits=ndigits)
        if isinstance(value, (float, int))
        else default
    )


def format_enum(value: Optional[Enum], default: str = "None") -> str:
    """Format an enum for logging in a table."""
    return format_str(value.value) if isinstance(value, Enum) else default


def format_conditional_message(
    value: bool, on_true: str = "True", on_false: str = "False"
) -> str:
    return format_str(on_true if bool(value) else on_false)


def format_func_name(value: Optional[Callable], default: str = "None") -> str:
    return format_str(value.__name__) if callable(value) else default
