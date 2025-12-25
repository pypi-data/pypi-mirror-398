import ast
from pathlib import Path
from os.path import dirname, abspath, join
from hestia_earth.schema import SchemaType
from hestia_earth.utils.api import find_node_exact, search
from hestia_earth.utils.model import linked_node
from hestia_earth.utils.tools import flatten, non_empty_list

from . import cached_value

ROOT_DIR = abspath(join(dirname(abspath(__file__)), ".."))
CACHE_SOURCES_KEY = "sources"


def _find_source(biblio_title: str = None):
    source = (
        find_node_exact(SchemaType.SOURCE, {"bibliography.title": biblio_title})
        if biblio_title
        else None
    )
    return (
        None
        if source is None
        else linked_node({"@type": SchemaType.SOURCE.value, **source})
    )


def get_source(node: dict, biblio_title: str = None, other_biblio_titles: list = []):
    source = cached_value(node, CACHE_SOURCES_KEY, {}).get(
        biblio_title
    ) or _find_source(biblio_title)
    other_sources = non_empty_list(
        [
            (
                cached_value(node, CACHE_SOURCES_KEY, {}).get(title)
                or _find_source(title)
            )
            for title in other_biblio_titles
        ]
    )
    return ({"source": source} if source else {}) | (
        {"otherSources": other_sources} if other_sources else {}
    )


def _parse_file_biblios(var_name: str, node: ast.Assign):
    try:
        value = ast.literal_eval(node.value)
        return (
            (
                [value]
                if isinstance(value, str)
                else [item for item in value if isinstance(item, str)]
            )
            if any([var_name == "BIBLIO_TITLE", var_name == "OTHER_BIBLIO_TITLES"])
            else []
        )
    except ValueError:
        pass
    return []


def _parse_file(content: str) -> list[str]:
    tree = ast.parse(content)
    return flatten(
        [
            (
                _parse_file_biblios(node.targets[0].id, node)
                if isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                else []
            )
            for node in tree.body
        ]
    )


def _extract(filepath: Path) -> list[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return _parse_file(content) if "BIBLIO_TITLE =" in content else []


def _list_sources():
    dir = Path(ROOT_DIR)
    # ignore current file
    files = list(
        filter(
            lambda f: not str(f).endswith("utils/source.py"), list(dir.rglob("**/*.py"))
        )
    )
    return list(set(flatten(map(_extract, files))))


def find_sources():
    titles = _list_sources()
    query = {
        "bool": {
            "must": [{"match": {"@type": SchemaType.SOURCE.value}}],
            "should": [
                {"match": {"bibliography.title.keyword": title}} for title in titles
            ],
            "minimum_should_match": 1,
        }
    }
    results = search(
        query, fields=["@type", "@id", "name", "bibliography.title"], limit=len(titles)
    )
    return {
        result.get("bibliography").get("title"): linked_node(result)
        for result in results
    }
