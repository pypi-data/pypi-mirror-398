import requests
import json
from packaging.version import Version as LooseVersion

from pygeai.core.utils.console import Console


def get_latest_version(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = json.loads(response.text)
        return data['info']['version']
    except requests.RequestException as e:
        Console.write_stderr(f"An error occurred while fetching the latest version: {e}")


def get_installed_version(package_name):
    try:
        import importlib.metadata
        installed_version = importlib.metadata.version(package_name)
        return installed_version
    except importlib.metadata.PackageNotFoundError:
        return "Not installed"
    except ModuleNotFoundError:
        Console.write_stderr("This Python installation does not support importlib.metadata. Use Python 3.8+ or install importlib_metadata manually.")
        return "Unknown"


def check_new_version(package_name):
    latest_version = get_latest_version(package_name)
    installed_version = get_installed_version(package_name)

    if latest_version is None or installed_version == "Unknown":
        return "Could not determine version information."

    if installed_version == "Not installed":
        return f"{package_name} is not installed, but the latest version available is {latest_version}."

    if LooseVersion(latest_version) > LooseVersion(installed_version):
        return f"There's a new version available: {latest_version}. You have {installed_version} installed."
    else:
        return f"You have the latest version {installed_version} of {package_name}."
