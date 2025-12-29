import sys
from functools import lru_cache

from lionweb.language import Annotation, Language, LionCoreBuiltins, Property
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.v1.ast_language import ast_language


@lru_cache(maxsize=1)
def comment_language() -> Language:
    lw_version = LIONWEB_VERSION_USED_BY_STARLASU

    language = Language(
        lion_web_version=lw_version, name="com.strumenta.starlasu.comments"
    )
    language.id = "com-strumenta-starlasu-comments"
    language.key = "starlasu-comments"
    language.version = "1"
    language.add_dependency(ast_language())

    comment = Annotation(lion_web_version=lw_version, name="Comment")
    comment.id = f"{language.id}-{comment.get_name()}"
    comment.key = comment.get_name()
    comment.annotates = LionCoreBuiltins.get_node(lw_version)
    language.add_element(comment)

    comment_text = Property(lion_web_version=lw_version, name="text")
    comment_text.type = LionCoreBuiltins.get_string(lw_version)
    comment_text.id = f"{language.id}-{comment.get_name()}-{comment_text.get_name()}"
    comment_text.key = f"{comment.get_name()}-{comment_text.get_name()}"
    comment.add_feature(comment_text)

    return language


@lru_cache(maxsize=1)
def comment_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(comment_language())


@lru_cache(maxsize=1)
def comment_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(comment_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "comment.language.v1.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(comment_language_str())
