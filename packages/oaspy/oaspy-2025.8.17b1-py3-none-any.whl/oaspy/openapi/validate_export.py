# -*- coding: utf-8 -*-

import os

import jmespath
from jmespath import exceptions as jmEexceptions

from ..utils import open_file, validate_json_schema


def validate_export(body):
    try:
        openapi_version = jmespath.search("openapi", body)

        if openapi_version is None:
            print("validate_export: an error occurred when reading the version from the file")
            print("validate_export: make sure that the file contains a definition of OpenApi")
            return None

        print(f"checking OpenApi version {openapi_version}...")

        if openapi_version.startswith("3.0."):
            schema_file = "openapi_v3.0x.json"
        elif openapi_version.startswith("3.1."):
            schema_file = "openapi_v3.1x.json"
        else:
            print("validate_export version not supported", openapi_version)
            return None

        current_directory = os.path.dirname(os.path.abspath(__file__))
        # print("current_directory:", current_directory)

        oas_data = os.path.join(current_directory, "schemas", schema_file)
        # print("schema_file:", schema_file)

        schema = open_file(oas_data)

        validate_json_schema(schema, body)

    except jmEexceptions.JMESPathError as jme:
        print("validate_export JMESPathError Exception:", jme)
    except Exception as e:
        print("validate_export Exception:", e)
