import sys
from functools import lru_cache

from lionweb.language import (Concept, Containment, Language, Property,
                              Reference)
from lionweb.language.lioncore_builtins import LionCoreBuiltins
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.utils import default_id, default_key
from starlasuspecs.v2.ast_language import ast_language


@lru_cache(maxsize=1)
def codebase_language() -> Language:
    CODEBASE_LANGUAGE = Language(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="Codebase",
        id="strumenta-codebase-v2",
        version="2",
        key="strumenta-codebase",
    )
    CODEBASE_LANGUAGE.add_dependency(ast_language())

    CODEBASE = Concept(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="Codebase",
        id="strumenta-codebase-concept-v2",
        key="strumenta-codebase-concept",
    )
    CODEBASE.set_partition(True)
    CODEBASE_LANGUAGE.add_element(CODEBASE)
    CODEBASE.add_implemented_interface(
        LionCoreBuiltins.get_inamed(LIONWEB_VERSION_USED_BY_STARLASU)
    )

    CODEBASE_FILES = Reference(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="files",
        id="strumenta-codebase-codebase-files-v2",
    )
    CODEBASE.add_feature(CODEBASE_FILES)
    CODEBASE_FILES.set_key("strumenta-codebase-codebase-files")
    CODEBASE_FILES.set_optional(True)
    CODEBASE_FILES.set_multiple(True)
    CODEBASE_FILES.set_type(CODEBASE)

    CODEBASE_FILE = Concept(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="CodebaseFile",
        id="strumenta-codebase-file-v2",
        key="strumenta-codebase-file",
    )
    CODEBASE_FILE.set_partition(True)
    CODEBASE_LANGUAGE.add_element(CODEBASE_FILE)

    CODEBASE_FILE_CODEBASE = Reference(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="codebase",
        id="strumenta-codebase-file-codebase-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_CODEBASE)
    CODEBASE_FILE_CODEBASE.set_key("strumenta-codebase-file-codebase")
    CODEBASE_FILE_CODEBASE.set_optional(False)
    CODEBASE_FILE_CODEBASE.set_multiple(False)
    CODEBASE_FILE_CODEBASE.set_type(CODEBASE)

    CODEBASE_FILE_LANGUAGE_NAME = Property(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="language_name",
        id="strumenta-codebase-file-language-name-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_LANGUAGE_NAME)
    CODEBASE_FILE_LANGUAGE_NAME.set_key("strumenta-codebase-file-language-name")
    CODEBASE_FILE_LANGUAGE_NAME.set_optional(False)
    CODEBASE_FILE_LANGUAGE_NAME.type = LionCoreBuiltins.get_string(
        LIONWEB_VERSION_USED_BY_STARLASU
    )

    CODEBASE_FILE_RELATIVE_PATH = Property(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="relative_path",
        id="strumenta-codebase-file-relative-path-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_RELATIVE_PATH)
    CODEBASE_FILE_RELATIVE_PATH.set_key("strumenta-codebase-file-relative-path")
    CODEBASE_FILE_RELATIVE_PATH.set_optional(False)
    CODEBASE_FILE_RELATIVE_PATH.type = LionCoreBuiltins.get_string(
        LIONWEB_VERSION_USED_BY_STARLASU
    )

    CODEBASE_FILE_CODE = Property(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="code",
        id="strumenta-codebase-file-code-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_CODE)
    CODEBASE_FILE_CODE.set_key("strumenta-codebase-file-code")
    CODEBASE_FILE_CODE.set_optional(False)
    CODEBASE_FILE_CODE.type = LionCoreBuiltins.get_string(
        LIONWEB_VERSION_USED_BY_STARLASU
    )

    CODEBASE_FILE_AST = Containment(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="ast",
        id="strumenta-codebase-file-ast-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_AST)
    CODEBASE_FILE_AST.set_key("strumenta-codebase-file-ast")
    CODEBASE_FILE_AST.set_optional(True)
    CODEBASE_FILE_AST.set_multiple(False)
    CODEBASE_FILE_AST.set_type(
        LionCoreBuiltins.get_node(LIONWEB_VERSION_USED_BY_STARLASU)
    )

    CODEBASE_FILE_ISSUES = Containment(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="issues",
        id="strumenta-codebase-file-issues-v2",
    )
    CODEBASE_FILE.add_feature(CODEBASE_FILE_ISSUES)
    CODEBASE_FILE_ISSUES.set_key("strumenta-codebase-file-issues")
    CODEBASE_FILE_ISSUES.set_optional(True)
    CODEBASE_FILE_ISSUES.set_multiple(True)
    CODEBASE_FILE_ISSUES.set_type(ast_language().get_concept_by_name("Issue"))

    tokens_list = ast_language().get_primitive_type_by_name("TokensList")

    CODEBASE_FILE_TOKENS = Property(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU, name="tokens"
    )
    CODEBASE_FILE_TOKENS.type = LionCoreBuiltins.get_string(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    CODEBASE_FILE_TOKENS.set_optional(True)
    CODEBASE_FILE_TOKENS.type = tokens_list
    CODEBASE_FILE.add_feature(CODEBASE_FILE_TOKENS)
    CODEBASE_FILE_TOKENS.id = default_id(CODEBASE_FILE_TOKENS)
    CODEBASE_FILE_TOKENS.key = default_key(CODEBASE_FILE_TOKENS)

    BUILTINS_COLLECTION = Concept(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="BuiltinsCollection",
        id="strumenta-codebase-builtins-collection-id-v2",
        key="strumenta-codebase-builtins-collection-key",
    )
    BUILTINS_COLLECTION.set_partition(True)
    CODEBASE_LANGUAGE.add_element(BUILTINS_COLLECTION)

    BUILTINS_COLLECTION_LANGUAGE_NAME = Property(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="languageName",
        id="strumenta-codebase-builtins-collection-language-name-id-v2",
    )
    BUILTINS_COLLECTION_LANGUAGE_NAME.key = (
        "strumenta-codebase-builtins-collection-language-name-key"
    )
    BUILTINS_COLLECTION_LANGUAGE_NAME.type = LionCoreBuiltins.get_string(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    BUILTINS_COLLECTION_LANGUAGE_NAME.set_optional(False)
    BUILTINS_COLLECTION.add_feature(BUILTINS_COLLECTION_LANGUAGE_NAME)

    BUILTINS_COLLECTION_BUILTINS = Containment(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name="builtins",
        id="strumenta-codebase-builtins-collection-builtins-id-v2",
    )
    BUILTINS_COLLECTION_BUILTINS.set_key(
        "strumenta-codebase-builtins-collection-builtins-key"
    )
    BUILTINS_COLLECTION_BUILTINS.set_type(
        LionCoreBuiltins.get_node(lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU)
    )
    BUILTINS_COLLECTION_BUILTINS.set_multiple(True)
    BUILTINS_COLLECTION_BUILTINS.set_optional(True)
    BUILTINS_COLLECTION.add_feature(BUILTINS_COLLECTION_BUILTINS)

    return CODEBASE_LANGUAGE


@lru_cache(maxsize=1)
def codebase_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(codebase_language())


@lru_cache(maxsize=1)
def codebase_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(codebase_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "codebase.language.v2.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(codebase_language_str())
