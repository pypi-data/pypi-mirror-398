import sys
from functools import lru_cache

from lionweb.language import (Classifier, Concept, Containment, DataType,
                              Language, LionCoreBuiltins, Property)
from lionweb.serialization import create_standard_json_serialization

from starlasuspecs.constants import LIONWEB_VERSION_USED_BY_STARLASU
from starlasuspecs.v1.ast_language import ast_language


def create_concept(name: str, partition: bool = False) -> Concept:
    CONCEPT = Concept(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU,
        name=name,
        id=f"strumenta-{name}-concept",
        key=f"{name}",
    )
    CONCEPT.set_partition(partition)
    return CONCEPT


def add_containment(
    container: Classifier,
    name: str,
    type: Classifier,
    optional: bool = False,
    many: bool = False,
) -> Containment:
    containment = Containment(LIONWEB_VERSION_USED_BY_STARLASU)
    containment.id = f"{container.id}-{name}"
    containment.key = f"{container.key}-{name}"
    containment.set_name(name)
    containment.set_type(type)
    containment.set_multiple(many)
    containment.set_optional(optional)

    container.add_feature(containment)
    return containment


def add_property(
    container: Classifier, name: str, type: DataType, optional: bool = False
) -> Property:
    property = Property(LIONWEB_VERSION_USED_BY_STARLASU)
    property.id = f"{container.id}-{name}"
    property.key = f"{container.key}-{name}"
    property.set_name(name)
    property.type = type
    property.set_optional(optional)

    container.add_feature(property)
    return property


@lru_cache(maxsize=1)
def pipeline_language() -> Language:
    lw_version = LIONWEB_VERSION_USED_BY_STARLASU

    language = Language(lion_web_version=lw_version, name="com.strumenta.Pipeline")
    language.id = "com-strumenta-Pipeline"
    language.key = "com_strumenta_pipeline"
    language.version = "1"
    language.add_dependency(ast_language())

    PIPELINE = create_concept("Pipeline", partition=True)
    language.add_element(PIPELINE)

    PIPELINE_STEP = create_concept("PipelineStep")
    language.add_element(PIPELINE_STEP)

    COMPONENT_USAGE = create_concept("ComponentUsage")
    language.add_element(COMPONENT_USAGE)

    COMPONENT_PARAM_CONFIGURATION = create_concept("ComponentParameterConfiguration")
    language.add_element(COMPONENT_PARAM_CONFIGURATION)

    METRIC = create_concept("Metric")
    METRIC.add_implemented_interface(
        LionCoreBuiltins.get_inamed(LIONWEB_VERSION_USED_BY_STARLASU)
    )
    language.add_element(METRIC)

    add_containment(PIPELINE, "steps", PIPELINE_STEP, optional=True, many=True)

    add_containment(
        PIPELINE_STEP, "usedComponents", COMPONENT_USAGE, optional=True, many=True
    )

    add_property(
        COMPONENT_USAGE,
        "componentName",
        LionCoreBuiltins.get_string(LIONWEB_VERSION_USED_BY_STARLASU),
        optional=False,
    )
    add_property(
        COMPONENT_USAGE,
        "componentVersion",
        LionCoreBuiltins.get_string(LIONWEB_VERSION_USED_BY_STARLASU),
        optional=False,
    )

    add_property(
        COMPONENT_PARAM_CONFIGURATION,
        "paramName",
        LionCoreBuiltins.get_string(LIONWEB_VERSION_USED_BY_STARLASU),
        optional=False,
    )
    add_property(
        COMPONENT_PARAM_CONFIGURATION,
        "paramValue",
        LionCoreBuiltins.get_string(LIONWEB_VERSION_USED_BY_STARLASU),
        optional=True,
    )

    add_property(
        METRIC,
        "value",
        LionCoreBuiltins.get_string(LIONWEB_VERSION_USED_BY_STARLASU),
        optional=True,
    )

    add_containment(
        COMPONENT_USAGE,
        "params",
        COMPONENT_PARAM_CONFIGURATION,
        optional=True,
        many=True,
    )

    add_containment(PIPELINE_STEP, "metrics", METRIC, optional=True, many=True)

    return language


@lru_cache(maxsize=1)
def pipeline_language_json():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_element(pipeline_language())


@lru_cache(maxsize=1)
def pipeline_language_str():
    jsonser = create_standard_json_serialization(
        lion_web_version=LIONWEB_VERSION_USED_BY_STARLASU
    )
    return jsonser.serialize_tree_to_json_string(pipeline_language())


if __name__ == "__main__":
    n_args = len(sys.argv)
    outfile = "pipeline.language.v1.json"
    if n_args == 2:
        outfile = sys.argv[1]
    elif n_args > 2:
        raise ValueError(f"Too many args: {sys.argv}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(pipeline_language_str())
