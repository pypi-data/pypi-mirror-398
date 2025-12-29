# -*- coding: utf-8 -*-

YAAK_VERSION = 4


def get_resources(res_list):
    """Recorrer los recursos y extraer segun
    el tipo."""
    groups = []

    folder_list = res_list.get("folders", None)

    for item in folder_list:
        groups.append(
            {
                "id": item["id"],
                "folderId": item["folderId"],
                "name": item["name"],
                "description": item.get("description", None),
            }
        )

    return {
        "work_space": res_list.get("workspaces", None),
        "envs": res_list.get("environments", None),
        "groups": groups,
        "requests": res_list.get("httpRequests", None),
        "cookie_jar": None,
        "api_spec": None,
    }


def validate_v4(yaak_data):
    """valida la estructura inicial
    del archivo json de Yaak
    """

    if "yaakVersion" in yaak_data:
        yaak_version = yaak_data.get("yaakVersion", None)

        if not yaak_version.startswith("2025"):
            print("the 'yaakVersion' key does not exist...")
            return None

        print("leyendo yaakVersion:", yaak_version)

    if "yaakSchema" in yaak_data:
        yaak_schema = yaak_data.get("yaakSchema", None)
        if yaak_schema != YAAK_VERSION:
            print("the 'yaak_schema' key does not exist...")
            return None

        print("leyendo yaak_schema:", yaak_schema)

    yaak_resources = None
    print("leyendo resources...")

    if "resources" in yaak_data:
        yaak_resources = yaak_data.get("resources", None)
        if not bool(yaak_resources):
            print("the 'resources' key does not exist...")
            return None

        workspaces = yaak_resources.get("workspaces", None)
        if workspaces is None or len(workspaces) <= 0:
            print("there are no workspaces...")
            return None
        print("loading workspaces:", len(workspaces))

        environments = yaak_resources.get("environments", None)
        if environments is None or len(environments) <= 0:
            print("there are no environments...")
            # return None
        print("loading environments:", len(environments))

        folders = yaak_resources.get("folders", None)
        if folders is None or len(folders) <= 0:
            print("there are no groups(folders)...")
            return None
        print("loading groups(folders):", len(folders))

        http_requests = yaak_resources.get("httpRequests", None)
        if http_requests is None or len(http_requests) <= 0:
            print("there are no http_requests...")
            return None
        print("loading http_requests:", len(http_requests))

    result = get_resources(yaak_resources)
    return result
