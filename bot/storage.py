import os
import json


def load_from_file(filename, default_value=None):
    if os.path.exists(filename):
        with open(filename) as file:
            try:
                return json.load(file)
            except:
                return default_value
    else:
        return default_value


def save_to_file(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
