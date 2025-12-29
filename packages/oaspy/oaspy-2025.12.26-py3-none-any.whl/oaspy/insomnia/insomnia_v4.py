# -*- coding: utf-8 -*-

INSO_VERSION = 4


def get_resources(res_list):
    # recorrer los recursos y extraer segun el tipo
    work_space = []
    cookie_jar = []
    api_spec = []
    envs = []
    groups = []
    requests = []

    for item in res_list:
        # print("item:", item)
        res_type = item["_type"]

        match res_type:
            case "workspace":
                work_space.append(item)
            case "cookie_jar":
                cookie_jar.append(item)
            case "api_spec":
                api_spec.append(item)
            case "environment":
                envs.append(item)
            case "request_group":
                groups.append(
                    {
                        "id": item["_id"],
                        "parentId": item["parentId"],
                        "name": item["name"],
                        "description": item["description"],
                    }
                )
            case "request":
                # print("loading request:", item["url"])
                requests.append(item)
            case _:
                print("unknown resource...", item)
                print()

    return {
        "work_space": work_space,
        "envs": envs,
        "groups": groups,
        "requests": requests,
        "cookie_jar": cookie_jar,
        "api_spec": api_spec,
    }


def validate_v4(inso_data):
    """valida la estructura inicial del archivo json"""
    resources = None

    if "_type" in inso_data:
        _type = inso_data["_type"]

        if _type != "export":
            print("the '_type' key does not exist...")
            return None

        print("leyendo _type:", _type)

    if "__export_format" in inso_data:
        export_format = inso_data["__export_format"]
        if export_format != INSO_VERSION:
            print("the '__export_format' key does not exist...")
            return None

        print("leyendo __export_format:", export_format)

    if "__export_source" in inso_data:
        export_source = inso_data["__export_source"]
        if "insomnia" not in export_source:
            print("the 'insomnia' key does not exist...")
            return None

        print("leyendo __export_source:", export_source)

    if "resources" in inso_data:
        resources = inso_data["resources"]
        if resources is None or len(resources) <= 0:
            print("there are no resources...")
            return None

        print("loading resources:", len(resources))

    result = get_resources(resources)
    return result
