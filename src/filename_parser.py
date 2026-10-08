import re
from pathlib import Path
from datetime import datetime


NORMAL_PATTERN = re.compile(
    r"^Chambers of Xeric\((\d+)\) "
    r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.png$",
    re.IGNORECASE
)

CM_PATTERN = re.compile(
    r"^Chambers of Xeric Challenge Mode\((\d+)\) "
    r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.png$",
    re.IGNORECASE
)


def parse_filename(file_path):
    """
    Extracts raid information from a RuneLite Boss Kills screenshot.
    """

    filename = Path(file_path).name

    # Challenge Mode
    match = CM_PATTERN.match(filename)

    if match:
        kc = int(match.group(1))
        date = match.group(2)
        time = match.group(3)

        timestamp = datetime.strptime(
            f"{date}_{time}",
            "%Y-%m-%d_%H-%M-%S"
        )

        return {
            "raid": "Chambers of Xeric",
            "mode": "CM",
            "kc": kc,
            "timestamp": timestamp
        }

    # Normal Mode
    match = NORMAL_PATTERN.match(filename)

    if match:
        kc = int(match.group(1))
        date = match.group(2)
        time = match.group(3)

        timestamp = datetime.strptime(
            f"{date}_{time}",
            "%Y-%m-%d_%H-%M-%S"
        )

        return {
            "raid": "Chambers of Xeric",
            "mode": "Normal",
            "kc": kc,
            "timestamp": timestamp
        }

    return None