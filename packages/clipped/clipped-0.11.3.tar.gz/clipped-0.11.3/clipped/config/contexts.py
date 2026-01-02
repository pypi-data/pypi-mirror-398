import os


def get_project_path(project_name: str) -> str:
    base_path = os.path.expanduser("~")
    if not os.access(base_path, os.W_OK):
        base_path = "/tmp"

    return os.path.join(base_path, project_name)


def get_temp_path(project_name: str) -> str:
    return os.path.join("/tmp", project_name)
