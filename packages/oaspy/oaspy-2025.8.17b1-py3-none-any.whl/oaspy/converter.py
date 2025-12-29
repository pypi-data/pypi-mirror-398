# -*- coding: utf-8 -*-

from .openapi import generate_spec_v30x, generate_spec_v31x
from .utils import save_file


def convert(file_name, from_schema=None, output_file=None, order_folder=False, order_request=False, coll_mode=None):
    if file_name is None:
        print("oaspy: unknow file_name...")
        print("exiting...")
        print()

    if coll_mode is None:
        print("oaspy error: unknow collection spec...")
        print("exiting...")
        print()

    result_oa3 = None

    if from_schema == "v30":
        result_oa3 = generate_spec_v30x(file_name, order_folder, order_request, coll_mode)
    elif from_schema == "v31":
        result_oa3 = generate_spec_v31x(file_name, order_folder, order_request, coll_mode)
    else:
        print(f"oaspy: unknow schema '{from_schema}' use any of the following arguments:")
        print("> oaspy gen -f collection_file_v4.json -s v30")
        print("for OpenApi Specification v3.0.x")
        print()
        print("> oaspy gen -f collection_file_v4.json -s v31")
        print("for OpenApi Specification v3.1.x")
        print("exiting...")
        print()
        return None

    if result_oa3 is not None:
        print(f"generando archivo de OpenApi {from_schema}...")
        output_file_name = output_file or f"export_openapi_{from_schema}.json"
        save_file(output_file_name, result_oa3)
