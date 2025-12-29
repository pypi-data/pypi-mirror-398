# -*- coding: utf-8 -*-

import os
import traceback
import unicodedata
from typing import Any

import orjson
from genson import SchemaBuilder
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, UnknownType, ValidationError


class DefaultTraceback(Exception):
    """Esta clase implementa un traceback sencillo
    para seguimiento de errores.

    No es necesario llamarla desde `print` ó `loguru`
    Sí desea una traza de error más completa, utilice
    `loguru` en su lugar.

    Examples:
        ```
        try:
            1 / 0
        except Exception as e:
            DefaultTraceback(e)
        ```
    """

    def __init__(self, exception: Exception):
        if exception is not None:
            print("DefaultTraceback error:")
            print("".join(traceback.format_exception(type(exception), value=exception, tb=exception.__traceback__)))


def open_file(file):
    print()
    try:
        print("open", file, "...")

        json_data = None
        so_encoding = "utf-8" if os.name == "nt" else None

        with open(file, "r", encoding=so_encoding) as f:
            json_data = orjson.loads(f.read())

        return json_data
    except Exception as e:
        print("open_file Exception:", e)


def save_file(file_name, data):
    try:
        # so_encoding = "utf-8" if os.name == "nt" else None
        # so_mode = "wb" if os.name == "nt" else "wb"
        #
        # print("so_encoding", so_encoding)
        # print("so_mode", so_mode)
        # print("file_name", file_name)
        # print("data", type(data))

        # with open(file_name, "w", encoding="utf-8") as f:
        # f.write(orjson.dumps(data).decode("utf-8"))
        with open(file_name, "wb") as f:  # modo binario, sin encoding
            f.write(orjson.dumps(data))

        print("Yep", file_name, "succesfully generated.")
    except Exception as e:
        print("save_file: Oops, definitely can not generate file...", e)


def check_file(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False


def is_iterable(value: Any) -> bool:
    if value is None:
        return False

    return isinstance(value, (tuple, list))


# def check_json_schema(schema):
#     try:
#         Draft202012Validator.check_schema(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
#         return True
#     except (ValidationError, SchemaError, UnknownType) as ve:
#         print("check_json_schema ValidationError: {}", ve)
#     except Exception as e:
#         print("ValidateSchema Exception:", e)
#     return False


def validate_json_schema(schema, body):
    try:
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        errors: list[Any] = sorted(validator.iter_errors(body), key=str)

        if not is_iterable(errors):
            raise Exception("error validating the error list")

        if len(errors) <= 0:
            print("JSON Schema Validator OK")
            return body

        missing: list[Any] = []

        for error in errors:
            obj_error: dict[str, Any] = {
                "absolute_path": list(error.absolute_path),
                "message": error.message,
                "validator": error.validator,
            }

            if "description" in error.schema:
                obj_error.update({"description": error.schema.get("description")})

            missing.append(obj_error)

        if len(missing) > 0:
            print("JSON Schema Validator errors:")
            print()
            print(missing)

    except (ValidationError, SchemaError, UnknownType) as ve:
        print("An instance was invalid under a provided schema...")
        print("ValidateSchema ValidationError: {}", ve)
    except Exception as e:
        print("ValidateSchema Exception:", e)


def remove_accents(unicode_str):
    if unicode_str is None:
        return None

    try:
        return "".join(
            (char_at for char_at in unicodedata.normalize("NFD", unicode_str) if unicodedata.category(char_at) != "Mn")
        )
    except Exception as e:
        print("remove_accents Exception:", e)
        return None


def clean_string(ugly_cad):
    if ugly_cad is None:
        return None

    special_list = [
        {"b": "á", "g": "a"},
        {"b": "é", "g": "e"},
        {"b": "í", "g": "i"},
        {"b": "ó", "g": "o"},
        {"b": "ú", "g": "u"},
        {"b": "Á", "g": "A"},
        {"b": "É", "g": "E"},
        {"b": "Í", "g": "I"},
        {"b": "Ó", "g": "O"},
        {"b": "Ú", "g": "U"},
        {"b": "ñ", "g": "n"},
        {"b": "Ñ", "g": "N"},
        {"b": "\xe1", "g": "a"},
        {"b": "\xe9", "g": "e"},
        {"b": "\xed", "g": "i"},
        {"b": "\xf3", "g": "o"},
        {"b": "\xfa", "g": "u"},
        {"b": "\xc1", "g": "A"},
        {"b": "\xc9", "g": "E"},
        {"b": "\xcd", "g": "I"},
        {"b": "\xd3", "g": "O"},
        {"b": "\xda", "g": "U"},
    ]

    try:
        for item in special_list:
            result = ugly_cad.replace(item["b"], item["g"])
            ugly_cad = result

        return ugly_cad

    except Exception as e:
        print("clean_string Exception:", e)
        return None


def full_strip(dirty_str, min_len=3):
    try:
        step1 = dirty_str.strip()
        step2 = clean_string(step1)
        step3 = remove_accents(step2)
        step4 = step3.replace(" ", "_")  # TO FIX
        clean_str = step4.replace("/", "_")  # TO FIX
        final_step = clean_str.strip()

        if len(final_step) < min_len:
            return None

        return final_step
    except Exception as e:
        print("full_strip Exception:", e)
        return None


def generate_json_schema(title, data):
    try:
        builder = SchemaBuilder()

        builder.add_schema({"type": "object", "title": title, "properties": {}})
        builder.add_object(data)

        result = builder.to_schema()
        # print(builder.to_json(indent=2))
        # remove '$schema' due openapi 3.0.x warnings
        result.pop("$schema", None)
        return result
    except Exception as e:
        print("generate_json_schema Exception:", e)
        return None


def check_input(body):
    if body is None:
        return None

    # check for Insomnia
    headers = body.get("__export_source", None)
    if headers is not None:
        if headers.startswith("insomnia"):
            return "inso"

    # check for Yaak
    headers = body.get("yaakSchema", None)
    if headers is not None:
        if headers == 4:
            return "yaak"

    return None
