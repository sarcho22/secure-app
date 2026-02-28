"""
JSON file read/write helpers.
"""

import json
import os


def load_json(path):
    """
    Generic JSON load helper.
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    """
    Generic JSON save helper.
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=4)