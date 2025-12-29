# -*- coding: utf-8 -*-

import re
from copy import deepcopy

import jmespath
import orjson
from jsf import JSF

from oaspy.openapi.httpcodes import HTTPCODES

from ..utils import DefaultTraceback, full_strip, generate_json_schema, open_file
from . import validate_v4

work_space = []
# envs = []
groups_list = []
# requests = []

# tags = []s
# paths = []
servers = []

cookie_jar = []
api_spec = []


schema_export = {
    "openapi": "3.0.3",
    "info": {
        "title": "awesome api - OpenAPI 3.0",
        "description": "my awesome api",
        "termsOfService": "http://awesome.io/terms",
        "contact": {"email": "apiteam@awesome.io"},
        "license": {"name": "MIT", "url": "https://opensource.org/license/mit/"},
        "x-logo": {"url": "https://redocly.github.io/redoc/petstore-logo.png"},
        "version": "1.0.0",
    },
    "externalDocs": {"description": "Find out more about OpenApi", "url": "https://www.openapis.org"},
    "paths": [],
    "servers": [],
    "tags": [],
    "x-tagGroups": [],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "description": "example: `Authorization: Bearer AWESOME_TOKEN_HERE`",
                "bearerFormat": "string",
            },
        },
        "schemas": {},
        "examples": {},
    },
}

default_responses = {
    "200": {"description": "successful"},
    "201": {"description": "created"},
    "400": {"description": "bad request"},
    "401": {"description": "authorization failed"},
    "403": {"description": "Forbidden"},
    "422": {"description": "validation failed"},
    "500": {"description": "unknown server error"},
}


def create_envs(envs_list=None):
    """create_envs(create_servers), procesa los entornos (envs)"""
    print("create envs...")
    servers_list = []

    try:
        for item in envs_list:
            variables = {}
            print("name:", item["name"])
            data = item["data"]
            obj = {
                "description": item["name"],
            }

            if data is not None:
                for key in data:
                    # print("item data key:", key)
                    variables[key] = {"default": str(data[key])}

            url = list(variables.keys())
            if len(url) > 0:
                first = url[0]
                obj["url"] = data[first]
                obj["variables"] = variables
                servers_list.append(obj)

        # print()
        # print("create_envs variables:", variables)
        # print()
        # print("create_envs servers_list:", servers_list)
        return servers_list
    except Exception as e:
        print("create_envsException...", e)
        return None


def create_groups():
    pass


def create_requests():
    pass


def comp_schema_body(desc_name, method, body):
    try:
        rename_desc = full_strip(desc_name.lower())
        title = "Generated schema for Root"
        schema_json = generate_json_schema(title, body)

        if schema_json is not None:
            new_schema_name = [f"{rename_desc}_{method}"][0]

            # print("comp_schema_body new_schema_name...", new_schema_name)
            data = {new_schema_name: schema_json}
            # print("comp_schema_body data...", data)

            return (new_schema_name, data)
    except Exception as e:
        print("comp_schema_body Exception...", e)
    return None, None


def create_tags(groups_list):
    # recorrer los grupos?
    print("create_tags processing tags")
    tag_list = []
    tag_groups = []

    for item in groups_list:
        if item["parentId"] != "":
            parent_name = next((x["name"] for x in groups_list if x["id"] == item["parentId"]), None)
            if parent_name:
                # Validar si el elemento actual tiene elementos anidados
                if not any(item["id"] == parent["parentId"] for parent in groups_list):
                    existing_tag = next((x for x in tag_groups if x["name"] == parent_name), None)
                    if existing_tag:
                        existing_tag["tags"].append(item["name"])
                    else:
                        tag_groups.append({"name": parent_name, "tags": [item["name"]]})

    if len(tag_groups) == 1:
        tag_groups = []

    for item in groups_list:
        item_name = item["name"] if "name" in item else "Missing group name"
        if not any(item["id"] == parent["parentId"] for parent in groups_list):
            tag_list.append(
                {
                    "name": item_name,
                    "description": item["description"] if "description" in item else item_name,
                }
            )

    return tag_list, tag_groups


def update_refs(json_obj):
    if isinstance(json_obj, dict):
        if "$ref" in json_obj:
            if json_obj["$ref"].startswith("#/components/schemas"):
                json_obj["$ref"] = json_obj["$ref"].replace("#/components/schemas", "#/definitions")
        for key, value in json_obj.items():
            update_refs(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            update_refs(item)


def update_max_values(json_obj):
    if isinstance(json_obj, dict):
        if "type" in json_obj:
            if json_obj["type"] == "string":
                minLength = json_obj.get("minLength")
                if minLength:
                    new_maxLength = minLength + 20
                    maxLength = json_obj.get("maxLength", 0)
                    if maxLength > new_maxLength:
                        json_obj["maxLength"] = new_maxLength
            if json_obj["type"] in ("integer", "number"):
                minimum = json_obj.get("minimum")
                if minimum:
                    new_maximum = minimum + 100
                    maximum = json_obj.get("maximum", 0)
                    if maximum > new_maximum:
                        json_obj["maximum"] = new_maximum
            if json_obj["type"] == "array":
                minItems = json_obj.get("minItems")
                if minItems:
                    new_maxItems = minItems + 5
                    maxItems = json_obj.get("maxItems", 0)
                    if maxItems > new_maxItems:
                        json_obj["maxItems"] = new_maxItems

                if "$ref" in json_obj.get("items", {}):
                    if "uniqueItems" in json_obj:
                        json_obj.pop("uniqueItems")

        for key, value in json_obj.items():
            update_max_values(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            update_max_values(item)


def get_schemas_desc(name, desc):
    main_info = None
    secundary_info = None
    response_status_schemas = {}
    response_status_examples = {}
    responses_obj = {}
    try:
        main_schema = r"<!-- MAIN-SCHEMA -->(.*?)<!-- END MAIN-SCHEMA -->"
        secundary_schema = r"<!-- SECUNDARY-SCHEMA -->(.*?)<!-- END SECUNDARY-SCHEMA -->"
        response_schema = r"<!-- RESPONSE {0} -->(.*?)<!-- END RESPONSE {0} -->"

        result_main_info = re.search(main_schema, desc, re.DOTALL)
        if result_main_info:
            main_info = result_main_info.group(1).strip()
            try:
                if main_info:
                    main_info = orjson.loads(main_info)
                    check = True  # check_json_schema(list(main_info.values())[0])
                    if main_info:
                        if not check:
                            main_info = None
                            print("invalid jsonschema at main_info")
                        else:
                            desc = re.sub(main_schema, "", desc, flags=re.DOTALL)
                    else:
                        main_info = None
                else:
                    main_info = None
            except Exception as e:
                main_info = None
                print(f"invalid json at main_info: {e}")

        if main_info:
            result_secundary_info = re.search(secundary_schema, desc, re.DOTALL)
            if result_secundary_info:
                secundary_info = result_secundary_info.group(1).strip()
                try:
                    if secundary_info:
                        secundary_info = orjson.loads(secundary_info)
                        if secundary_info:
                            for key, value in secundary_info.items():
                                check = True  # check_json_schema(value)
                                if not check:
                                    print(f"invalid jsonschema at secundary_info {key}")
                                    secundary_info = None
                                else:
                                    desc = re.sub(secundary_schema, "", desc, flags=re.DOTALL)
                        else:
                            secundary_info = None
                    else:
                        secundary_info = None
                except Exception as e:
                    secundary_info = None
                    print(f"invalid json at secundary_info: {e}")

        for i in HTTPCODES.keys():
            response_status_schema = response_schema.format(i)
            result_response_status = re.search(response_status_schema, desc, re.DOTALL)
            if result_response_status:
                response_status = result_response_status.group(1).strip()
                try:
                    if response_status:
                        response_status = orjson.loads(response_status)
                        check = True  # check_json_schema(list(response_status.values())[0])
                        if response_status:
                            if not check:
                                print("invalid jsonschema at responses_obj")
                            else:
                                desc = re.sub(response_status_schema, "", desc, flags=re.DOTALL)
                                response_status_schemas.update({f"{name}_{i}": response_status})
                                update_max_values(response_status)
                                response_faker = JSF(response_status)
                                response_fake_json = response_faker.generate(use_defaults=True, use_examples=True)
                                response_status_examples.update({f"{name}_{i}": {"value": response_fake_json}})
                                responses_obj.update(
                                    {
                                        f"{i}": {
                                            "description": response_status.get("description", HTTPCODES.get(i)),
                                            "content": {
                                                "application/json": {
                                                    "schema": {"$ref": f"#/components/schemas/{name}_{i}"},
                                                    "examples": {
                                                        f"{name}_{i}": {"$ref": f"#/components/examples/{name}_{i}"}
                                                    },
                                                }
                                            },
                                        }
                                    }
                                )
                except Exception:
                    desc = re.sub(response_status_schema, "", desc, flags=re.DOTALL)
                    responses_obj.update(
                        {
                            f"{i}": {
                                "description": HTTPCODES.get(i),
                                "content": {"text/plain": {"schema": {"type": "string"}, "example": response_status}},
                            }
                        }
                    )

    except Exception as e:
        print("get_schemas_desc Exception...", e)
    return desc, main_info, secundary_info, responses_obj, response_status_schemas, response_status_examples


def create_paths(requests_list, groups_list=None):
    """procesa la lista de requests y groups"""
    try:
        print("processing requests...")
        request_paths = {}

        for key, item in enumerate(requests_list):
            parent_id = item["parentId"] if "parentId" in item else None
            desc_name = item["name"]
            dirty_url = item["url"]

            new_url = re.sub(r"\{\{.*?\}\}", "", dirty_url)
            method = item["method"].lower()

            _endpoint = [new_url][0].strip()
            _method = [method][0]
            _group = None

            desc = item["description"] if "description" in item else None
            desc, main_info, secundary_info, custom_responses, rss, rse = get_schemas_desc(
                f"schema_{key}_{desc_name}", desc
            )

            if custom_responses:
                responses = custom_responses
                schema_export["components"]["schemas"].update(rss)
                schema_export["components"]["examples"].update(rse)
            else:
                responses = default_responses

            if _endpoint is None or _endpoint == "" or _endpoint.startswith(("http", "https")):
                print(f"skipping (invalid endpoint): {_method.upper()} -> '{_endpoint[:25]}...' (desc: '{desc_name}')")
                continue

            if parent_id is not None:
                _group = next((d.get("name") for d in groups_list if d.get("id") == parent_id), "default")

            obj_request = {
                _endpoint: {
                    _method: {
                        "description": desc if desc is not None else "description not available",
                        "summary": desc_name,
                        "tags": [_group],
                        "operationId": f"op_{_method}_{key}",
                        "parameters": [
                            {
                                "name": "Accept-Encoding",
                                "schema": {"type": "string", "example": "gzip, deflate", "format": "string"},
                                "in": "header",
                            }
                        ],
                        "security": [{"bearerAuth": []}],  # TO FIX
                        "responses": responses,
                    }
                }
            }

            if _method in {"post", "put", "patch"}:
                body = item["body"] if "body" in item else None

                if body is not None and bool(body) is True:
                    mime_type = body["mimeType"] if "mimeType" in body else None
                    request_body = {}

                    match mime_type:
                        case "application/json":
                            example = body["text"] if "text" in body else None

                            if not example:
                                print(f"skipping (missing request body): {_method.upper()} -> '{desc_name}'")
                                continue

                            try:
                                example = orjson.loads(example)
                            except Exception:
                                print(f"invalid json at: {_method.upper()}->'{desc_name}'")
                                example = str(example)

                            # se crea un json_schema del request body
                            schema_name = f"schema_{key} {desc_name}"
                            if main_info:
                                rename_desc = full_strip(schema_name.lower())
                                ref_path = [f"{rename_desc}_{_method}"][0]
                                request_schema = list(main_info.values())[0]
                                jsonschema_faker = deepcopy(request_schema)

                                if secundary_info is not None:
                                    jsonschema_faker.update({"definitions": deepcopy(secundary_info)})
                                    # se agrega el json_schema del body al components/schemas
                                    schema_export["components"]["schemas"].update(secundary_info)

                                update_refs(jsonschema_faker)
                                update_max_values(jsonschema_faker)
                                try:
                                    request_faker = JSF(jsonschema_faker)
                                    request_fake_json = request_faker.generate(use_defaults=True, use_examples=True)
                                except Exception:
                                    print(
                                        f"can't generate fake data body: {_method.upper()}->'{desc_name} {_endpoint}'"
                                    )
                                    request_fake_json = {}

                                result_schema = {ref_path: request_schema}
                                request_body = {
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            mime_type: {
                                                "schema": {"$ref": f"#/components/schemas/{ref_path}"},
                                                "examples": {f"{ref_path}": {"value": request_fake_json}},
                                            }
                                        },
                                    },
                                }
                                schema_export["components"]["schemas"].update(result_schema)
                            else:
                                ref_path, result_schema = comp_schema_body(schema_name, _method, example)
                                request_body = {
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            mime_type: {"schema": {"$ref": f"#/components/schemas/{ref_path}"}}
                                        },
                                    },
                                }
                                schema_export["components"]["schemas"].update(result_schema)

                            if ref_path is None:
                                request_body = {
                                    "requestBody": {
                                        "required": True,
                                        "content": {mime_type: {}},
                                    },
                                }

                        case "multipart/form-data":
                            params = body["params"] if "params" in body else None

                            if not params:
                                print(f"skipping (missing multipart/form-data): {_method.upper()} -> '{desc_name}'")
                                continue

                            obj_form = {}

                            for item in params:
                                disabled = False
                                obj = {}

                                if "disabled" in item:
                                    disabled = item["disabled"]

                                if disabled is False:
                                    if "type" in item:
                                        if item["type"] == "file":
                                            obj: dict[str, str] = {"type": "string", "format": "binary"}
                                            obj_form["file"] = obj
                                        else:
                                            obj: dict[str, str] = {"type": "string", "format": "text"}
                                            name = item["name"]
                                            obj_form[name] = obj
                                    else:
                                        name = [item["name"]][0]
                                        obj = {"type": "string", "format": "uuid"}
                                        obj_form[name] = obj

                            request_body = {
                                "requestBody": {
                                    "required": True,
                                    "content": {
                                        mime_type: {
                                            "schema": {
                                                "type": "object",
                                                "properties": obj_form,
                                            }
                                        }
                                    },
                                },
                            }
                        case _:
                            print(f"skipping (unknown mime_type): {_method.upper()} -> '{desc_name}'")
                            continue

                    # esto agrega el request body como ejemplo
                    # de la solicitud
                    obj_request[_endpoint][_method].update(request_body)
                else:
                    print(f"skipping (missing body): {_method.upper()} -> '{desc_name}'")
                    continue

            request_paths.update(obj_request)
            obj_request = {}

        print()
        return request_paths
    except Exception as e:
        print("create_paths Exception...", e)
        print(jsonschema_faker)
        DefaultTraceback(e)
        return None


def get_info_openapi(json_data):
    try:
        workspace_desc = jmespath.search("resources[?_type=='workspace'].description", json_data)
        info_openapi = r"<!-- INFO OPENAPI -->(.*?)<!-- END INFO OPENAPI -->"
        if workspace_desc:
            result_info_openapi = re.search(info_openapi, workspace_desc[0], re.DOTALL)
            if result_info_openapi:
                info_openapi = result_info_openapi.group(1).strip()
                try:
                    if info_openapi:
                        info_openapi = orjson.loads(info_openapi)
                        if info_openapi:
                            schema_export.update(info_openapi)
                            # desc = re.sub(info_openapi, '', desc, flags=re.DOTALL)
                except Exception as e:
                    print(f"invalid json at get_info_openapi: {e}")
    except Exception as e:
        print(f"invalid json at get_info_openapi: {e}")


def create_schema(json_data, order_folder, order_request):
    if "servers" in json_data:
        schema_export["servers"] = json_data["servers"]

    if "paths" in json_data:
        if order_request:
            # Sort the keys alphabetically
            sorted_keys = sorted(json_data["paths"].keys())

            # create a new dictionary with sorted keys
            schema_export["paths"] = {key: json_data["paths"][key] for key in sorted_keys}
        else:
            schema_export["paths"] = json_data["paths"]

    if "tags" in json_data:
        if order_folder:
            schema_export["tags"] = sorted(json_data["tags"], key=lambda x: x["name"])
        else:
            schema_export["tags"] = json_data["tags"]

    if "x-tagGroups" in json_data:
        if order_folder:
            for folder in json_data["x-tagGroups"]:
                folder.get("tags", []).sort()
            schema_export["x-tagGroups"] = sorted(json_data["x-tagGroups"], key=lambda x: x["name"])
        else:
            schema_export["x-tagGroups"] = json_data["x-tagGroups"]

    return schema_export


# TO FIX
def inso_gen_v30x(file_name, order_folder, order_request):
    """lee un archivo de insomnia v4"""

    json_data = open_file(file_name)
    # resources = None

    if json_data is None:
        print("generate_v30x: failed to read json_data")
        return None

    resources = validate_v4(json_data)

    get_info_openapi(json_data)

    print("ready to process...")
    # print(resources)
    # print("======================")

    envs_result = create_envs(resources["envs"])
    # print("create_envs:", envs_result)
    tags_result, tag_groups_result = create_tags(resources["groups"])
    groups_list = resources["groups"]
    # print("=============groups=============")
    # print(groups)
    # print("=============groups=============")
    paths_result = create_paths(resources["requests"], groups_list)

    create_schema(
        {"servers": envs_result, "tags": tags_result, "x-tagGroups": tag_groups_result, "paths": paths_result},
        order_folder,
        order_request,
    )
    print("listo!...")

    # print("=================================")
    # print(schema_export)
    return schema_export
