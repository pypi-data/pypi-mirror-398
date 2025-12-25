_KEYS = ["impacts", "endpoints"]


def _has_value(blank_node: dict):
    return blank_node.get("value") is not None


def _filter_has_value(impact: dict, key: str):
    return list(filter(_has_value, impact[key]))


def run(impact: dict):
    return impact | {
        key: _filter_has_value(impact, key) for key in _KEYS if impact.get(key)
    }
