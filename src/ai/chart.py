import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from threading import Lock
import copy
import logging
import pickle
from lxml import html
import time
import traceback

logger = logging.getLogger(__name__)

LANGUAGES = {
    "LangIc-1": "Java",
    "LangIc-2": "C++",
    # "LangIc-3": "Java",
    # "LangIc-4": "Java",
    "LangIc-5": "C#",
    # "LangIc-6": "Java",
    "LangIc-7": "Python 2",
    # "LangIc-8": "Java",
    "LangIc-9": "Python 3",
    # "LangIc-10": "Java",
    "LangIc-11": "Pascal",
    "LangIc-12": "D",
    "LangIc-13": "C++ 11",
    "LangIc-14": "C",
    "LangIc-15": "Ruby",
    # "LangIc-16": "Java",
    "LangIc-17": "Scala",
    # "LangIc-18": "Java",
    "LangIc-19": "Kotlin",
    "LangIc-20": "C++ 14",
    "LangIc-21": "Go",
    "LangIc-22": "JS",
    # "LangIc-23": "Java",
    "LangIc-25": "Swift",
    "LangIc-26": "Rust",
    "LangIc-27": "Nim",
    "LangIc-28": "PyPy2",
    # "LangIc-29": "PyPy2",
    "LangIc-30": "PyPy3",
}


class Player:
    def __init__(self, username, language, games_count, winrate, score, delta):
        self.games_count = games_count
        self.winrate = winrate
        self.score = score
        self.delta = delta
        self.username = username
        self.language = language


class Chart:
    def __init__(self, url, expiration_time):
        self._lock = Lock()
        self._url = url
        self.name = None
        self._top_players = []
        self._players = []
        self._expiration_time = expiration_time
        self._last_top_update_time = 0
        self._last_all_update_time = 0

    def _update_top(self):
        if time.time() - self._last_top_update_time < self._expiration_time:
            return

        with self._lock:
            logger.info("Updating top of ai chart...")
            page_places, page_players = self.grab_standings_page(1)
            self._top_players = page_players
            logger.info("Top of ai chart updated")

    def _update_all(self):
        if time.time() - self._last_all_update_time < self._expiration_time:
            return

        with self._lock:
            logger.info("Updating all ai chart...")
            self._players.clear()
            page = 1
            last_parse_place = None
            while True:
                page_places, page_players = self.grab_standings_page(page)
                if last_parse_place == page_places[-1]:
                    break

                self._players += page_players
                last_parse_place = page_places[-1]
                page += 1

            self._last_update_time = time.time()
            logger.info("All ai chart updated")

    def grab_standings_page(self, page):
        players = []
        places = []
        logger.info(f"Parsing standings page {page} for url {self._url}")

        page = requests.get(f"{self._url}page/{page}?locale=ru")
        tree = html.fromstring(page.content)
        self.name = " ".join(tree.xpath("//div[@class='breadcrumb']")[0].text_content().split())
        for tr in tree.xpath('//div[@class="commonBottom"]/table/tbody/tr'):
            try:
                tc = tr.text_content().split()
                if tc[3] == '/':
                    del tc[3:5]
                lng_icon = tr.xpath(".//span[contains(@class, 'lc')]/@class")[0].split()[1]
                language = LANGUAGES.get(lng_icon, "?")
                place = tc[0]
                places.append(place)
                player = Player(username=tc[1],
                                language=language,
                                games_count=tc[2],
                                winrate=tc[3],
                                score=tc[4],
                                delta=tc[5])
                players.append(player)
            except BaseException:
                logger.error(f"Couldn't parse player tr: {html.tostring(tr)}")
                logger.error(traceback.format_exc())

        return places, players

    def get_top(self, n):
        self._update_top()
        return list(map(copy.deepcopy, self._top_players[:n]))

    def get_pos(self, usernames):
        self._update_all()
        usernames = set(u.lower() for u in usernames)
        result = []
        for place, player in enumerate(self._players):
            p_name = player.username.lower()
            if any(substring in p_name for substring in usernames):
                result.append((place, copy.deepcopy(player)))
        return result
