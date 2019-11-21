import logging

logger = logging.getLogger(__name__)

import os

__all__ = ['config']


class Config:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "")
        self.tg_token = os.getenv("TG_TOKEN", "")
        self.port = int(os.getenv("PORT", "8443"))
        self.host = os.getenv("HOST", "")
        self.admins = os.getenv("BOT_ADMINS", "").split()

        self.forum_rss_url = "http://russianaicup.ru/forum/index.php?action=.xml;type=rss"
        self.forum_refresh_delay = 120
        self.forum_notify_delay = 1 * 60 * 60

    def __str__(self):
        return f"Config<tg_token:...{self.tg_token[-3:]} " + \
               f"host:{self.host}" + \
               f"port:{self.port}" + \
               ">"

config = Config()

try:
    from local_settings import *
except ImportError:
    pass

