#!/usr/bin/env python
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Mapping, MutableMapping, cast, TypedDict

import click
import yaml
from jsonref import JsonRef  # type: ignore

from .errors import UnsupportedError
from .log import debug, error, info
from .util import (
    additional_properties,
    allow_null_optional_fields,
    append_no_duplicates,
    change_dict_values,
    replace_int_or_string,
)

# ---- Type aliases for JSON-like data ----
JSONScalar = str | int | float | bool | None
JSON = Dict[str, Any] | List[Any] | JSONScalar
JSONObj = Dict[str, Any]
JSONMap = Mapping[str, Any]


# Optional: a light TypedDict for kube extension entries you index into repeatedly
class KubeGVK(TypedDict, total=False):
    group: str
    version: str
    kind: str


@click.command()
@click.option(
    "-o",
    "--output",
    default="schemas",
    metavar="PATH",
    help="Directory to store schema files",
)
@click.option(
    "-p",
    "--prefix",
    default="_definitions.json",
    help="Prefix for JSON references (only for OpenAPI versions before 3.0)",
)
@click.option(
    "--stand-alone", is_flag=True, help="Whether or not to de-reference JSON schemas"
)
@click.option(
    "--expanded", is_flag=True, help="Expand Kubernetes schemas by API version"
)
@click.option(
    "--kubernetes", is_flag=True, help="Enable Kubernetes specific processors"
)
@click.option(
    "--strict",
    is_flag=True,
    help="Prohibits properties not in the schema (additionalProperties: false)",
)
@click.argument("schema", metavar="SCHEMA_URL")
def default(
    output: str,
    schema: str,
    prefix: str,
    stand_alone: bool,
    expanded: bool,
    kubernetes: bool,
    strict: bool,
) -> None:
    """
    Converts a valid OpenAPI specification into a set of JSON Schema files.
    """
    info("Downloading schema")

    # Resolve local files to file:// URL; otherwise request via HTTP(S)
    if os.path.isfile(schema):
        schema_url: str = "file://" + os.path.realpath(schema)
    else:
        schema_url = schema

    req = urllib.request.Request(schema_url)
    response = urllib.request.urlopen(req)  # nosec: B310 (tooling-controlled input)

    info("Parsing schema")
    # YAML loader returns 'Any'
    data_any: Any = yaml.load(response.read(), Loader=yaml.SafeLoader)

    # We expect the root to be a dict
    data: JSONObj = cast(JSONObj, data_any)

    # Extract version as string
    version_val: Any = data.get("swagger") if "swagger" in data else data.get("openapi")
    version: str = cast(str, version_val)

    if not os.path.exists(output):
        os.makedirs(output)

    if version < "3":
        # OpenAPI 2 (Swagger) shared definitions
        definitions_any: Any = data["definitions"]
        definitions: JSONObj = cast(JSONObj, definitions_any)

        if kubernetes:
            # Extend definitions with Kubernetes-specific conveniences
            definitions["io.k8s.apimachinery.pkg.util.intstr.IntOrString"] = {
                "oneOf": [{"type": "string"}, {"type": "integer"}]
            }
            definitions["io.k8s.apimachinery.pkg.api.resource.Quantity"] = {
                "oneOf": [{"type": "string"}, {"type": "number"}]
            }

            # Populate apiVersion/kind enums from x-kubernetes-group-version-kind
            for _, type_def_any in list(definitions.items()):
                type_def = cast(JSONObj, type_def_any)
                if "x-kubernetes-group-version-kind" in type_def:
                    gvk_list_any: Any = type_def["x-kubernetes-group-version-kind"]
                    gvk_list: List[KubeGVK] = cast(List[KubeGVK], gvk_list_any)
                    for kube_ext in gvk_list:
                        if (
                            expanded
                            and "properties" in type_def
                            and "apiVersion" in type_def["properties"]
                        ):
                            api_version = (
                                f"{kube_ext.get('group','')}/{kube_ext.get('version','')}"
                                if kube_ext.get("group")
                                else kube_ext.get("version", "")
                            )
                            append_no_duplicates(
                                cast(JSONObj, type_def["properties"]["apiVersion"]),
                                "enum",
                                api_version,
                            )
                        if (
                            "properties" in type_def
                            and "kind" in type_def["properties"]
                        ):
                            kind_val = kube_ext.get("kind", "")
                            append_no_duplicates(
                                cast(JSONObj, type_def["properties"]["kind"]),
                                "enum",
                                kind_val,
                            )

        if strict:
            definitions = additional_properties(
                cast(MutableMapping[str, Any], definitions)
            )

        with open(f"{output}/_definitions.json", "w") as definitions_file:
            info("Generating shared definitions")
            definitions_file.write(json.dumps({"definitions": definitions}, indent=2))

    info("Generating individual schemas")
    types: List[str] = []

    # Components/schemas root differs across OAS versions
    if version < "3":
        components_any: Any = data["definitions"]
    else:
        comps_any: Any = data["components"]
        comps = cast(JSONObj, comps_any)
        components_any = comps["schemas"]
    components: JSONObj = cast(JSONObj, components_any)

    for title, spec_any in components.items():
        title_str: str = title
        specification: JSONObj = cast(JSONObj, spec_any)

        kind = title_str.split(".")[-1].lower()
        if kubernetes:
            # Guard split depth — assuming Kubernetes style titles
            parts = title_str.split(".")
            if len(parts) >= 3:
                group = parts[-3].lower()
                api_version = parts[-2].lower()
            else:
                group = "core"
                api_version = "v1"
        else:
            group = ""
            api_version = ""

        specification["$schema"] = "http://json-schema.org/schema#"
        specification.setdefault("type", "object")

        if strict:
            specification["additionalProperties"] = False

        if kubernetes and expanded:
            if group in {"core", "api"}:
                full_name = f"{kind}-{api_version}"
            else:
                full_name = f"{kind}-{group}-{api_version}"
        else:
            full_name = kind

        types.append(title_str)

        try:
            debug(f"Processing {full_name}")

            if kubernetes:
                parts = title_str.split(".")
                # These APIs are deprecated (pkg namespace)
                if len(parts) > 3 and parts[3] == "pkg" and parts[2] == "kubernetes":
                    raise UnsupportedError(
                        f"{title_str} not currently supported, due to use of pkg namespace"
                    )

            # Skip troublesome CRD schema shapes when stand-alone
            if (
                kubernetes
                and stand_alone
                and kind
                in {
                    "jsonschemaprops",
                    "jsonschemapropsorarray",
                    "customresourcevalidation",
                    "customresourcedefinition",
                    "customresourcedefinitionspec",
                    "customresourcedefinitionlist",
                    "jsonschemapropsorstringarray",
                    "jsonschemapropsorbool",
                }
            ):
                raise UnsupportedError(f"{kind} not currently supported")

            # Normalize $ref values
            specification = change_dict_values(specification, prefix, version)

            # Resolve $ref in-place if requested
            if stand_alone:
                base = f"file://{os.getcwd()}/{output}/"
                specification = cast(
                    JSONObj, JsonRef.replace_refs(specification, base_uri=base)  # type: ignore
                )

            # Recurse into additionalProperties if present
            if "additionalProperties" in specification:
                ap_any: Any = specification["additionalProperties"]
                if ap_any:
                    specification["additionalProperties"] = change_dict_values(
                        cast(JSONObj, ap_any), prefix, version
                    )

            # Strict mode: disallow extras inside properties
            if strict and "properties" in specification:
                props_any: Any = specification["properties"]
                specification["properties"] = additional_properties(
                    cast(MutableMapping[str, Any], props_any)
                )

            # Kubernetes-specific transforms
            if kubernetes and "properties" in specification:
                props_any = specification["properties"]
                props_obj = cast(JSONObj, props_any)
                updated = replace_int_or_string(props_obj)
                updated = cast(JSONObj, allow_null_optional_fields(updated))
                specification["properties"] = updated

            out_path = f"{output}/{full_name}.json"
            with open(out_path, "w") as schema_file:
                debug(f"Generating {full_name}.json")
                schema_file.write(json.dumps(specification, indent=2))

        except Exception as e:
            error(f"An error occurred processing {kind}: {e}")

    # Aggregate all types into a meta schema
    all_path = f"{output}/all.json"
    with open(all_path, "w") as all_file:
        info("Generating schema for all types")
        contents: JSONObj = {"oneOf": []}
        one_of: List[JSONObj] = contents["oneOf"]  # type: ignore[index]
        for title in types:
            if version < "3":
                one_of.append({"$ref": f"{prefix}#/definitions/{title}"})
            else:
                one_of.append(
                    {"$ref": title.replace("#/components/schemas/", "") + ".json"}
                )
        all_file.write(json.dumps(contents, indent=2))
