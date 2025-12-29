# -*- coding: utf-8 -*-

import jmespath
from jmespath import exceptions as jmEexceptions

from ..utils import validate_json_schema

schema_yaak_beta = {
    "$id": "https://example.com/tree",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "description": "Yaak Collection 2025.1.0-beta.15",
    "type": "object",
    "required": ["yaakVersion", "yaakSchema", "timestamp", "resources"],
    "properties": {
        "yaakVersion": {"type": "string", "minLength": 3},
        "yaakSchema": {"type": "integer", "minimum": 0, "enum": [4]},
        "timestamp": {"type": "string", "minLength": 10},
        "resources": {
            "type": "object",
            "properties": {
                "workspaces": {"$ref": "#/definitions/arrayItems", "description": "workspaces"},
                "environments": {"$ref": "#/definitions/arrayEnvs", "description": "environments"},
                "folders": {"$ref": "#/definitions/arrayItems", "description": "folders"},
                "httpRequests": {"$ref": "#/definitions/arrayItems", "description": "httpRequests"},
                "grpcRequests": {"type": "array"},
                "websocketRequests": {"type": "array"},
            },
        },
    },
    "definitions": {
        "arrayItems": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "description": "question data items",
                "minProperties": 1,
            },
        },
        "arrayEnvs": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "description": "enviromenrs items",
                "minProperties": 1,
            },
        },
    },
    "additionalProperties": False,
}


def get_info(body):
    """Shows information from an Yaak Beta file.

    Args:
        body ([dict]): json data from file
    """

    print("Validating JSON Schema for Yaak...")

    result = validate_json_schema(schema_yaak_beta, body)

    if result is None:
        return None

    try:
        _yaak_version = jmespath.search("yaakVersion", body)
        _yaakschema = jmespath.search("yaakSchema", body)
        _export_date = jmespath.search("timestamp", body)

        _workspace = jmespath.search("resources.workspaces", body)
        _environment = jmespath.search("resources.environments", body)
        # _api_spec = jmespath.search("resources.folders", body)
        _request_group_folders = jmespath.search("resources.folders", body)
        _request = jmespath.search("length(resources.httpRequests)", body)

        # _cookie_jar = jmespath.search("resources[?_type=='cookie_jar']|[0]", body)
        _request_get = jmespath.search("length(resources.httpRequests[?method=='GET'])", body)
        _request_post = jmespath.search("length(resources.httpRequests[?method=='POST'])", body)
        _request_put = jmespath.search("length(resources.httpRequests[?method=='PUT'])", body)
        _request_delete = jmespath.search("length(resources.httpRequests[?method=='DELETE'])", body)
        _request_patch = jmespath.search("length(resources.httpRequests[?method=='PATCH'])", body)

        # length(resources.httpRequests[?bodyType && bodyType == `application/json`])
        _request_json = jmespath.search(
            "length(resources.httpRequests[?headers && headers[?value == 'application/json']])", body
        )
        _request_form_data = jmespath.search(
            "length(resources.httpRequests[?headers && headers[?value == 'multipart/form-data']])", body
        )
        _request_unknow = jmespath.search("length(resources.httpRequests[?!headers])", body)

        print()
        print("===Yaak version===")
        print(_yaak_version)

        print("===Yaak schema===")
        print(_yaakschema)

        print("===Yaak export===")
        print("export date:", _export_date)

        print()
        print("===Yaak workspace===")
        if _workspace is not None:
            for worksp in _workspace:
                print("workspace name:", worksp.get("name", None))
                descrip = worksp.get("description", None)
                if descrip is not None and descrip:
                    print("workspace description:", descrip)
                else:
                    print("workspace description: 'description is empty'")
        else:
            print("no workspace")

        # TO CHECK
        # print()
        # print("===Yaak api_spec===")
        # if _api_spec is not None:
        #     print("api_spec name:", _api_spec.get("fileName", None))
        # else:
        #     print("no api_spec")

        # TO CHECK
        # print("===Yaak cookie_jar===")
        # if _cookie_jar is not None:
        #     print("cookie_jar name:", _cookie_jar.get("name", None))
        #     print("cookie_jar cookies:", _cookie_jar.get("cookies", None))
        # else:
        #     print("no cookie jar")

        print()
        print("===Yaak environments===")
        print(len(_environment))

        for item in _environment:
            print("- name:", item.get("name", None))
            print("- public:", item.get("public", False))

        print()
        print("===Yaak request groups(folders)===")
        print(len(_request_group_folders))

        for item in _request_group_folders:
            print("- request name:", item.get("name", None))
            descrip = item.get("description", None)
            if descrip is not None and descrip:
                print("description:", descrip)
            else:
                print("description: 'description is empty'")

        print()
        print("===request Methods===")
        print(_request)
        if _request_get is not None:
            print("- GET:", _request_get)
        if _request_post is not None:
            print("- POST:", _request_post)
        if _request_put is not None:
            print("- PUT:", _request_put)
        if _request_delete is not None:
            print("- DELETE:", _request_delete)
        if _request_patch is not None:
            print("- PATCH:", _request_patch)

        print()
        print("===request using application/json===")
        print(_request_json)

        print()
        print("===request using multipart/form-data===")
        print(_request_form_data)
        _request_form_data = jmespath.search(
            "resources.httpRequests[?headers && headers[?value == 'multipart/form-data']]", body
        )
        if _request_form_data is not None:
            for item in _request_form_data:
                print("-", item.get("method", "Unknow method"), item.get("name", None))

        print()
        print("===request headers unknow===")
        print(_request_unknow)
        _request_unknow = jmespath.search("resources.httpRequests[?!headers]", body)
        if _request_unknow is not None:
            for item in _request_unknow:
                print("-", item.get("method", "Unknow method"), item.get("name", None))

    except jmEexceptions.JMESPathError as jme:
        print("Yaak get_info JMESPathError Exception:", jme)
    except Exception as e:
        print("Yaak get_info Exception:", e)

    return None
