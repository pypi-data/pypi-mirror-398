import subprocess
import sys
from typing import List, Optional
import requests
from packaging.version import parse as parse_version
import json
import logging
from importlib.metadata import version
from .install import get_pip_command


def last_version(package: str):
    """Check if last version"""
    url = f"""https://pypi.org/pypi/{package}/json"""  # noqa: E231
    req = requests.get(url)
    version = parse_version("0")
    if req.status_code == requests.codes.ok:
        j = json.loads(req.text.encode(req.encoding))
        releases = j.get("releases", [])
        for release in releases:
            ver = parse_version(release)
            if not ver.is_prerelease:
                version = max(version, ver)
    return version


def check_last(package: str) -> Optional[str]:
    pypi = last_version(package)
    current = parse_version(version(package))
    if pypi > current:
        return pypi


def check_last_mastermind(args: List[str]):
    better_version = check_last("su_master_mind")

    if better_version:
        logging.info("Updating the package to version %s", better_version)

        # Import Configuration here to avoid circular imports
        from .configuration import Configuration

        # Get configured courses to include in the update
        config = Configuration()
        courses = sorted(config.courses)

        # Build the package specification with extras
        if courses:
            extras = ",".join(courses)
            package_spec = f"su_master_mind[{extras}]=={better_version}"
        else:
            package_spec = f"su_master_mind=={better_version}"

        # Get the pip command
        pip_cmd = get_pip_command()

        # Install the updated package
        cmd = pip_cmd + [package_spec]
        logging.info(f"Running: {' '.join(cmd)}")

        try:
            subprocess.check_call(cmd)
            logging.info("Update successful, restarting command")
            subprocess.check_call(args)
            sys.exit()
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update: {e}")
            sys.exit(1)
