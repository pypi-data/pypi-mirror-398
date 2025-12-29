from typing import Optional

from lionweb.language import IKeyed, INamed, Language
from lionweb.model import Node


def lw_id_cleaned_version(s: str) -> str:
    return s.replace(".", "_").replace(" ", "_").replace("/", "_")


def id_prefix_for_contained_elements(node: Node) -> str:
    if node.id is None:
        raise ValueError("Node must have an id")
    return node.id.removeprefix("language-").removesuffix("-id")


def id_for_contained_element(node: Node, contained_element_name: str) -> str:
    return f"{id_prefix_for_contained_elements(node)}-{lw_id_cleaned_version(contained_element_name)}-id"


def default_id(node: Node) -> str:
    curr: Optional[Node] = node
    while curr is not None and not isinstance(curr, Language):
        curr = curr.get_parent()
    suffix = ""
    if curr is not None and curr.get_version() != "1":
        suffix = f"-{curr.get_version()}"
    parent = node.get_parent()
    if parent is None:
        raise ValueError("Node must have a parent to get a default id")
    if not isinstance(node, INamed):
        raise ValueError("Node must have a name")
    name = node.get_name()
    if name is None:
        raise ValueError("Node must have a name")
    return f"{id_prefix_for_contained_elements(parent)}-{lw_id_cleaned_version(name)}{suffix}-id"


def key_prefix_for_contained_elements(keyed: IKeyed) -> str:
    return keyed.get_key().removeprefix("language-").removesuffix("-key")


def key_for_contained_element(keyed: IKeyed, contained_element_name: str) -> str:
    return f"{key_prefix_for_contained_elements(keyed)}-{lw_id_cleaned_version(contained_element_name)}-key"


def default_key(node: Node) -> str:
    parent = node.get_parent()
    if parent is None:
        raise ValueError("Node must have a parent to get a default key")
    if not isinstance(parent, IKeyed):
        raise ValueError("Node must have a parent which is keyed to get a default key")
    if not isinstance(node, INamed):
        raise ValueError("Node must have a name")
    name = node.get_name()
    if name is None:
        raise ValueError("Node must have a name")
    return (
        f"{key_prefix_for_contained_elements(parent)}-{lw_id_cleaned_version(name)}-key"
    )
