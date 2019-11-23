import os
import logging

logger = logging.getLogger(__name__)


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
        self.game_notify_delay = 3 * 60
        self.ai_chart_refresh_delay = 60
        self.ai_chart_url = os.getenv("AI_CHART_URL",
                                      "https://russianaicup.ru/contest/1/standings/")
        self.ai_games_url = os.getenv("AI_GAMES_URL", "http://russianaicup.ru/contest/1/games/")

    def __str__(self):
        return f"Config<tg_token:...{self.tg_token[-3:]} " + \
               f"host:{self.host}" + \
               f"port:{self.port}" + \
               ">"


try:
    from local_settings import *
except ImportError:
    pass
