# -*- coding: utf-8 -*-

from ..insomnia import inso_gen_v30x, inso_gen_v31x
from ..yaak import yaak_gen_v30x


# TO FIX
def generate_spec_v30x(file_name, order_folder, order_request, coll_mode):
    """Genera el spec dato en version 3.0.x"""

    schema_export = None

    if coll_mode == "inso":
        schema_export = inso_gen_v30x(file_name, order_folder, order_request)
        return None
    elif coll_mode == "yaak":
        # print("oaspy yaak_gen_v30x error: yaak not allowed yet")
        schema_export = yaak_gen_v30x(file_name, order_folder, order_request)

    if schema_export is None:
        print("oaspy generate_spec_v30x internal error...")
        return None

    return schema_export


# TODO
def generate_spec_v31x(file_name, order_folder, order_request, coll_mode):
    """Genera el spec dato en version 3.1.x"""

    schema_export = None

    if coll_mode == "inso":
        schema_export = inso_gen_v31x(file_name, order_folder, order_request)
        if schema_export is None:
            print("oaspy inso_gen_v31x error: ")
            return None
    elif coll_mode == "yaak":
        schema_export = yaak_gen_v30x(file_name, order_folder, order_request)
        if schema_export is None:
            print("oaspy yaak_gen_v31x error: ")
            return None

    return schema_export
