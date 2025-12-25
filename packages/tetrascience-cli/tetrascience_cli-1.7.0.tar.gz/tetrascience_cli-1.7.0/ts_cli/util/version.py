import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree

import requests

from ts_cli.util.emit import emit_warning


def is_release_version(version: str) -> bool:
    return bool(re.search(r"^\d+\.\d+\.\d+$", version))


def get_latest_version():
    try:
        response = requests.get(
            "https://pypi.org/rss/project/tetrascience-cli/releases.xml", timeout=5
        )
        root = ElementTree.fromstring(response.content)
        versions = [title.text for title in root.findall("channel/item/title")]
        releases = [
            version.strip()
            for version in versions
            if version and is_release_version(version)
        ]
        return releases[0]
    except:
        return "0.0.0"


def check_update_required(current_version) -> None:
    try:
        latest_version_path = Path(
            os.path.join(Path.home(), ".config/tetrascience/ts-cli-latest.txt")
        )

        # refresh saved latest version once per day
        if (
            latest_version_path.is_file()
            and time.time() - latest_version_path.stat().st_mtime < 24 * 3600
        ):
            latest_version = latest_version_path.read_text(encoding="utf-8")
        else:
            latest_version = get_latest_version()
            latest_version_path.write_text(latest_version, encoding="utf-8")

        if latest_version and check_versions_for_update(
            current_version, latest_version
        ):
            emit_warning(
                f"Please upgrade ts-cli (local: {current_version}, latest: {latest_version})"
            )
            emit_warning("Use: pip install tetrascience-cli --upgrade\n")

    except Exception:
        return


def check_versions_for_update(current: str, latest: str):
    current_major, current_minor, *_rest = current.split(".")
    latest_major, latest_minor, *_rest = latest.split(".")
    if int(current_major) < int(latest_major):
        return True
    if (int(current_major) == int(latest_major)) and (
        int(current_minor) < int(latest_minor)
    ):
        return True
    return False
