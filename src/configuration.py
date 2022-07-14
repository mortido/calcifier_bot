import json
import os
from collections import namedtuple

CalciferConfig = namedtuple('CalciferConfig', ('tg_token', 'bot_admins', 'persistent_file', 'horse_chat'))


def from_json_file(filename):
    with open(filename) as f:
        content = json.load(f)

    return CalciferConfig(**content)
