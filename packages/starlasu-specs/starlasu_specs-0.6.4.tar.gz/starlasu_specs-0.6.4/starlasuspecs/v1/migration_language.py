import sys
from functools import lru_cache

from lionweb.language import Annotation, Language, Reference
from lionweb.language.lioncore_builtins import LionCoreBuiltins
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.v1.ast_language import ast_language


@lru_cache(maxsize=1)
def migration_language() -> Language:
    MIGRATION_LANGUAGE = Language(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="Code Migration",
        id="strumenta-migration",
        version="1.2",
        key="strumenta-migration",
    )
    MIGRATION_LANGUAGE.add_dependency(ast_language())

    ORIGINAL_ANNOTATION = Annotation(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="OriginalElement",
        id="strumenta-migration-original-element",
        key="original-element",
    )
    MIGRATION_LANGUAGE.add_element(ORIGINAL_ANNOTATION)
    ORIGINAL_ANNOTATION.annotates = LionCoreBuiltins.get_node(
        LIONWEB_VERSION_USED_BY_STARLASU
    )
    ORIGINAL_ANNOTATION_ELEMENT = Reference(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="element",
        id="strumenta-migration-original-element-element",
    )
    ORIGINAL_ANNOTATION_ELEMENT.set_key("original-element-element")
    ORIGINAL_ANNOTATION_ELEMENT.set_optional(False)
    ORIGINAL_ANNOTATION_ELEMENT.set_multiple(True)
    ORIGINAL_ANNOTATION_ELEMENT.set_type(
        LionCoreBuiltins.get_node(LIONWEB_VERSION_USED_BY_STARLASU)
    )
    ORIGINAL_ANNOTATION.add_feature(ORIGINAL_ANNOTATION_ELEMENT)

    MIGRATED_ANNOTATION = Annotation(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="MigratedElements",
        id="strumenta-migration-migrated-elements",
        key="migrated-elements",
    )
    MIGRATION_LANGUAGE.add_element(MIGRATED_ANNOTATION)
    MIGRATED_ANNOTATION.annotates = LionCoreBuiltins.get_node(
        LIONWEB_VERSION_USED_BY_STARLASU
    )
    MIGRATED_ANNOTATION_ELEMENTS = Reference(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="elements",
        id="strumenta-migration-migrated-elements-elements",
    )
    MIGRATED_ANNOTATION_ELEMENTS.set_key("original-element-elements")
    MIGRATED_ANNOTATION_ELEMENTS.set_optional(False)
    MIGRATED_ANNOTATION_ELEMENTS.set_multiple(True)
    MIGRATED_ANNOTATION_ELEMENTS.set_type(
        LionCoreBuiltins.get_node(LIONWEB_VERSION_USED_BY_STARLASU)
    )
    MIGRATED_ANNOTATION.add_feature(MIGRATED_ANNOTATION_ELEMENTS)

    DROPPED_ANNOTATION = Annotation(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="DroppedElement",
        id="strumenta-migration-dropped-element",
        key="dropped-element",
    )
    DROPPED_ANNOTATION.annotates = LionCoreBuiltins.get_node(
        LIONWEB_VERSION_USED_BY_STARLASU
    )
    MIGRATION_LANGUAGE.add_element(DROPPED_ANNOTATION)

    return MIGRATION_LANGUAGE


@lru_cache(maxsize=1)
def migrated_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(migration_language())


@lru_cache(maxsize=1)
def migrated_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(migration_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "migration.language.v1.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(migrated_language_str())
