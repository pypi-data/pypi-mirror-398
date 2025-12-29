import sys
from functools import lru_cache
from typing import Any

from lionweb.language import (Annotation, Classifier, Concept, Containment,
                              Enumeration, EnumerationLiteral, Interface,
                              Language, LionCoreBuiltins, PrimitiveType,
                              Property, Reference)
from lionweb.self.lioncore import LionCore
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.utils import (default_id, default_key,
                                 id_for_contained_element,
                                 key_for_contained_element)


def _add_placeholder_node_annotation(language: Language, ast_node: Classifier[Any]):
    lw_version = language.get_lionweb_version()

    suffix = f"-{language.get_version()}"

    placeholder_node_id = id_for_contained_element(language, "PlaceholderNode")
    placeholder_node = Annotation(
        lion_web_version=lw_version,
        language=language,
        name="PlaceholderNode",
        id=placeholder_node_id,
        key=key_for_contained_element(language, "PlaceholderNode"),
    )
    placeholder_node.annotates = LionCore.get_concept(lw_version)
    language.add_element(placeholder_node)

    annotation_type = Enumeration(
        lion_web_version=lw_version, name="PlaceholderNodeType"
    )
    language.add_element(annotation_type)
    annotation_type.id = (
        f"{placeholder_node_id.removesuffix('-id')}-PlaceholderNodeType{suffix}-id"
    )
    annotation_type.key = (
        f"{placeholder_node.key.removesuffix('-key')}-PlaceholderNodeType-key"
    )

    missing_ast_transformation = EnumerationLiteral(
        lion_web_version=lw_version,
        enumeration=annotation_type,
        name="MissingASTTransformation",
    )
    annotation_type.add_literal(missing_ast_transformation)
    missing_ast_transformation.id = default_id(missing_ast_transformation)
    missing_ast_transformation.key = "com-strumenta-Starlasu-PlaceholderNode-PlaceholderNodeType-id-MissingASTTransformation-key"

    failing_ast_transformation = EnumerationLiteral(
        lion_web_version=lw_version,
        enumeration=annotation_type,
        name="FailingASTTransformation",
    )
    annotation_type.add_literal(failing_ast_transformation)
    failing_ast_transformation.id = default_id(failing_ast_transformation)
    failing_ast_transformation.key = "com-strumenta-Starlasu-PlaceholderNode-PlaceholderNodeType-id-FailingASTTransformation-key"

    original_node = Reference(lion_web_version=lw_version, name="originalNode")
    placeholder_node.add_feature(original_node)
    original_node.id = (
        f"{placeholder_node_id.removesuffix('-id')}-originalNode{suffix}-id"
    )
    original_node.key = f"{placeholder_node.key.removesuffix('-key')}-originalNode-key"
    original_node.set_type(ast_node)
    original_node.set_optional(True)
    original_node.set_multiple(False)

    type_prop = Property(lion_web_version=lw_version, name="type")
    placeholder_node.add_feature(type_prop)
    type_prop.id = f"{placeholder_node_id.removesuffix('-id')}-type{suffix}-id"
    type_prop.key = f"{placeholder_node.key.removesuffix('-key')}-type-key"
    type_prop.type = annotation_type
    type_prop.set_optional(False)

    message_prop = Property(lion_web_version=lw_version, name="message")
    placeholder_node.add_feature(message_prop)
    message_prop.id = f"{placeholder_node_id.removesuffix('-id')}-message{suffix}-id"
    message_prop.key = f"{placeholder_node.key.removesuffix('-key')}-message-key"
    message_prop.type = LionCoreBuiltins.get_string(lw_version)
    message_prop.set_optional(False)


@lru_cache(maxsize=1)
def ast_language() -> Language:
    lw_version = LIONWEB_VERSION_USED_BY_STARLASU

    language = Language(lion_web_version=lw_version, name="com.strumenta.Starlasu")
    language.id = "com-strumenta-Starlasu-v2"
    language.key = "com_strumenta_starlasu"
    language.version = "2"

    char = PrimitiveType(lion_web_version=lw_version, language=language, name="Char")
    language.add_element(char)
    char.id = default_id(char)
    char.key = default_key(char)

    point = PrimitiveType(lion_web_version=lw_version, language=language, name="Point")
    language.add_element(point)
    point.id = default_id(point)
    point.key = default_key(point)

    position = PrimitiveType(
        lion_web_version=lw_version, language=language, name="Position"
    )
    language.add_element(position)
    position.id = default_id(position)
    position.key = default_key(position)

    ast_node = Interface(lion_web_version=lw_version, name="ASTNode")
    language.add_element(ast_node)
    ast_node.id = default_id(ast_node)
    ast_node.key = default_key(ast_node)

    ast_node_position = Property(lion_web_version=lw_version, name="position")
    ast_node.add_feature(ast_node_position)
    ast_node_position.id = default_id(ast_node_position)
    ast_node_position.key = default_key(ast_node_position)
    ast_node_position.type = position
    ast_node_position.set_optional(True)

    ast_node_original_node = Reference(lion_web_version=lw_version, name="originalNode")
    ast_node.add_feature(ast_node_original_node)
    ast_node_original_node.id = default_id(ast_node_original_node)
    ast_node_original_node.key = default_key(ast_node_original_node)
    ast_node_original_node.set_optional(True)
    ast_node_original_node.set_multiple(False)
    ast_node_original_node.set_type(ast_node)

    ast_node_transpiled_nodes = Reference(
        lion_web_version=lw_version, name="transpiledNodes"
    )
    ast_node.add_feature(ast_node_transpiled_nodes)
    ast_node_transpiled_nodes.id = default_id(ast_node_transpiled_nodes)
    ast_node_transpiled_nodes.key = default_key(ast_node_transpiled_nodes)
    ast_node_transpiled_nodes.set_optional(True)
    ast_node_transpiled_nodes.set_multiple(True)
    ast_node_transpiled_nodes.set_type(ast_node)

    _add_placeholder_node_annotation(language, ast_node)

    common_element = Interface(lion_web_version=lw_version, name="CommonElement")
    language.add_element(common_element)
    common_element.id = default_id(common_element)
    common_element.key = default_key(common_element)
    for name in [
        "BehaviorDeclaration",
        "Documentation",
        "EntityDeclaration",
        "EntityGroupDeclaration",
        "Expression",
        "Parameter",
        "PlaceholderElement",
        "Statement",
        "TypeAnnotation",
    ]:
        i = Interface(lion_web_version=lw_version, name=name)
        i.add_extended_interface(common_element)
        language.add_element(i)
        i.id = default_id(i)
        i.key = default_key(i)

    issue = Concept(lion_web_version=lw_version, name="Issue")
    language.add_element(issue)
    issue.id = default_id(issue)
    issue.key = default_key(issue)

    suffix = f"-{language.get_version()}"

    issue_type_enum = Enumeration(
        lion_web_version=lw_version, language=language, name="IssueType"
    )
    language.add_element(issue_type_enum)
    issue_type_enum.id = f"com-strumenta-Starlasu_IssueType{suffix}"
    issue_type_enum.key = "IssueType"
    for name in ["LEXICAL", "SYNTACTIC", "SEMANTIC", "TRANSLATION"]:
        literal = EnumerationLiteral(lion_web_version=lw_version, name=name)
        issue_type_enum.add_literal(literal)
        literal.id = f"com-strumenta-Starlasu_IssueType-{name}"
        literal.key = f"IssueType-{name}"

    issue_severity_enum = Enumeration(
        lion_web_version=lw_version, language=language, name="IssueSeverity"
    )
    language.add_element(issue_severity_enum)
    issue_severity_enum.id = f"com-strumenta-Starlasu_IssueSeverity{suffix}"
    issue_severity_enum.key = "IssueSeverity"
    for name in ["ERROR", "WARNING", "INFO"]:
        literal = EnumerationLiteral(lion_web_version=lw_version, name=name)
        issue_severity_enum.add_literal(literal)
        literal.id = f"com-strumenta-Starlasu_IssueSeverity-{name}{suffix}"
        literal.key = f"IssueSeverity-{name}"

    issue_type = Property(lion_web_version=lw_version, name="type")
    issue_type.type = issue_type_enum
    issue.add_feature(issue_type)
    issue_type.id = default_id(issue_type)
    issue_type.key = default_key(issue_type)

    issue_message = Property(lion_web_version=lw_version, name="message")
    issue_message.type = LionCoreBuiltins.get_string(lion_web_version=lw_version)
    issue.add_feature(issue_message)
    issue_message.id = default_id(issue_message)
    issue_message.key = default_key(issue_message)

    issue_severity = Property(lion_web_version=lw_version, name="severity")
    issue_severity.type = issue_severity_enum
    issue.add_feature(issue_severity)
    issue_severity.id = default_id(issue_severity)
    issue_severity.key = default_key(issue_severity)

    issue_position = Property(lion_web_version=lw_version, name="position")
    issue_position.type = position
    issue_position.set_optional(True)
    issue.add_feature(issue_position)
    issue_position.id = default_id(issue_position)
    issue_position.key = default_key(issue_position)

    tokens_list = PrimitiveType(lion_web_version=lw_version, name="TokensList")
    language.add_element(tokens_list)
    tokens_list.id = default_id(tokens_list)
    tokens_list.key = default_key(tokens_list)

    parsing_result = Concept(lion_web_version=lw_version, name="ParsingResult")
    language.add_element(parsing_result)
    parsing_result.id = default_id(parsing_result)
    parsing_result.key = default_key(parsing_result)

    parsing_result_issues = Containment(lion_web_version=lw_version, name="issues")
    parsing_result_issues.set_type(issue)
    parsing_result_issues.set_optional(True)
    parsing_result_issues.set_multiple(True)
    parsing_result.add_feature(parsing_result_issues)
    parsing_result_issues.id = default_id(parsing_result_issues)
    parsing_result_issues.key = default_key(parsing_result_issues)

    parsing_result_root = Containment(lion_web_version=lw_version, name="root")
    parsing_result_root.set_type(ast_node)
    parsing_result_root.set_optional(True)
    parsing_result_root.set_multiple(False)
    parsing_result.add_feature(parsing_result_root)
    parsing_result_root.id = default_id(parsing_result_root)
    parsing_result_root.key = default_key(parsing_result_root)

    parsing_result_code = Property(lion_web_version=lw_version, name="code")
    parsing_result_code.type = LionCoreBuiltins.get_string(lion_web_version=lw_version)
    parsing_result_code.set_optional(True)
    parsing_result.add_feature(parsing_result_code)
    parsing_result_code.id = default_id(parsing_result_code)
    parsing_result_code.key = default_key(parsing_result_code)

    parsing_result_tokens = Property(lion_web_version=lw_version, name="tokens")
    parsing_result_tokens.type = LionCoreBuiltins.get_string(
        lion_web_version=lw_version
    )
    parsing_result_tokens.set_optional(True)
    parsing_result_tokens.type = tokens_list
    parsing_result.add_feature(parsing_result_tokens)
    parsing_result_tokens.id = default_id(parsing_result_tokens)
    parsing_result_tokens.key = default_key(parsing_result_tokens)

    return language


@lru_cache(maxsize=1)
def ast_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(ast_language())


@lru_cache(maxsize=1)
def ast_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(ast_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "ast.language.v2.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(ast_language_str())
