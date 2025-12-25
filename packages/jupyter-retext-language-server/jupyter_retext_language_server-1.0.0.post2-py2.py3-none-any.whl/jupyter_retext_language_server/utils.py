import pathlib
import sysconfig


def get_shared_data_path():
    if hasattr(sysconfig, "get_default_scheme"):
        scheme = sysconfig.get_default_scheme()
    else:
        scheme = sysconfig._get_default_scheme()
    path = sysconfig.get_paths(scheme=scheme)["data"]
    return pathlib.Path(path) / "share"
