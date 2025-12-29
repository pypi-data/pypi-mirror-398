import sys
from functools import lru_cache

from lionweb.language import (Language, LanguageFactory, LionCoreBuiltins,
                              Multiplicity)
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.v1.ast_language import ast_language


@lru_cache(maxsize=1)
def type_language() -> Language:
    lf = LanguageFactory(
        lw_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="com.strumenta.starlasu.types",
        id="com-strumenta-starlasu-types",
    )
    # Add interface
    i = lf.interface("Type")
    # Add annotation
    lf.annotation(
        "TypeAnnotation",
        LionCoreBuiltins.get_node(LIONWEB_VERSION_USED_BY_STARLASU),
        key="com-strumenta-starlasu-types_TypeAnnotation",
    ).containment("type", i, Multiplicity.REQUIRED)

    language = lf.build()
    language.add_dependency(ast_language())
    return language


@lru_cache(maxsize=1)
def type_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(type_language())


@lru_cache(maxsize=1)
def type_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(type_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "type.language.v1.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(type_language_str())
