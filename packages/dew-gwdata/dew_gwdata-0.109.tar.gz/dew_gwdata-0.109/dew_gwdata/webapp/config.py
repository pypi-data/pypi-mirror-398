from pathlib import Path

import appdirs
import toml

WEB_APP_HOST = "bunyip"
WEB_APP_PORT = "8191"


def get_webapp_config_filename():
    folder = Path(appdirs.user_data_dir("dew_gwdata", "DEW"))
    folder.mkdir(parents=True, exist_ok=True)
    filename = "webapp_config.toml"
    path = folder / filename
    return path


def register_webapp_address(host, port):
    """Register and store the URL of the expected location of where the dew_gwdata webapp is."""
    path = get_webapp_config_filename()
    if path.is_file():
        with open(path, "r") as f:
            data = toml.load(f)
    else:
        data = {}
    data["host"] = host
    data["port"] = port
    with open(path, "w") as f:
        toml.dump(data, f)
    return True


def retrieve_webapp_address():
    """Return the host and port (if any) of where the dew_gwdata webapp is expected to be running."""
    path = get_webapp_config_filename()
    if path.is_file():
        with open(path, "r") as f:
            data = toml.load(f)
    else:
        data = {}
    return data.get("host", "localhost"), data.get("port", 8000)
