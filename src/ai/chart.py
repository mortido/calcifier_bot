import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from threading import Lock
import copy
import logging
from typing import List
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
    "LangIc-java": "Java",
    "LangIc-cpp": "C++",
    "LangIc-csharp": "C#",
    "LangIc-python": "Python",
    "LangIc-pascal": "Pascal",
    "LangIc-dlang": "D",
    "LangIc-c": "C",
    "LangIc-ruby": "Ruby",
    "LangIc-scala": "Scala",
    "LangIc-kotlin": "Kotlin",
    "LangIc-go": "Go",
    "LangIc-javascript": "JS",
    "LangIc-swift": "Swift",
    "LangIc-rust": "Rust",
    "LangIc-nim": "Nim",
}

STANDINGS_XPATH_TR = '//div[@class="commonBottom"]/table/tbody/tr'
GAMES_XPATH_GAME = '//div[@class="commonBottom"]/table/tbody/tr'


class Player:
    def __init__(self, username, language, games_count, winrate, score, delta):
        self.games_count = games_count
        self.winrate = winrate
        self.score = score
        self.delta = delta
        self.username = username
        self.language = language


class Game:
    def __init__(self, gid, token, gtype, players, scores, deltas, places, global_places):
        self.gid = gid
        self.token = token
        self.gtype = gtype
        self.players = players
        self.scores = scores
        self.deltas = deltas
        self.places = places
        self.global_places = global_places


class Chart:
    def __init__(self, standing_url, games_url, expiration_time):
        self._lock = Lock()
        self._standing_url = standing_url
        self._games_url = games_url
        self._last_game = None
        self.name = None
        self._top_players = []
        self._players = []
        self._places = {}
        self._expiration_time = expiration_time
        self._last_top_update_time = 0
        self._last_all_update_time = 0
        self._min_game_id = 0
        self._min_game_id = self._get_latest_game_id()

    def _update_top(self):
        if time.time() - self._last_top_update_time < self._expiration_time:
            return

        with self._lock:
            logger.info("Updating top of ai chart...")
            page_places, page_players = self.grab_standings_page(1)
            self._top_players = page_players
            logger.info("Top of ai chart updated")

    def _update_all(self, force=False):
        if not force and (time.time() - self._last_all_update_time < self._expiration_time):
            return

        with self._lock:
            logger.info("Updating all ai chart...")
            self._players.clear()
            self._places.clear()
            page = 1
            last_parse_place = None
            while True:
                page_places, page_players = self.grab_standings_page(page)
                if last_parse_place == page_places[-1]:
                    break

                self._players += page_players
                for place, player in zip(page_places, page_players):
                    self._places[player.username] = place
                last_parse_place = page_places[-1]
                page += 1

            self._last_update_time = time.time()
            logger.info("All ai chart updated")

    def grab_standings_page(self, page):
        players = []
        places = []
        url = f"{self._standing_url}page/{page}?locale=ru"
        logger.info(f"Parsing standings page {url}")

        page = requests.get(url)
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

    def get_new_games(self) -> List[Game]:
        page = 1
        games = []
        self._update_all(force=True)
        while True:
            end_reached, page_games = self._grab_games_page(page)
            page += 1
            games += page_games
            if end_reached:
                break
        return games

    def reset_to_game(self, game_id):
        self._min_game_id = game_id

    def _get_latest_game_id(self):
        url = f"{self._games_url}"
        logger.info(f"Parsing games page {url} to get latest game id")

        page = 1
        games = []
        while True:
            end_reached, games = self._grab_games_page(page)
            page += 1
            if end_reached or len(games) > 0:
                break
        return games[0].gid if len(games) > 0 else 0

    def _grab_games_page(self, page):
        games = []
        url = f"{self._games_url}page/{page}"
        logger.info(f"Parsing games page {url}")
        page = requests.get(url)
        tree = html.fromstring(page.content)
        end_reached = False
        try:
            for tr in tree.xpath(GAMES_XPATH_GAME):
                tds = tr.xpath("td")
                game_id = int(tds[0].text_content().strip())

                if self._min_game_id and game_id <= self._min_game_id:
                    end_reached = True
                    break

                if "Game is testing now" in tr.text_content() or "Game is in queue" in tr.text_content():
                    logger.info("Skipping game {}, still testing".format(game_id))
                    new_start = game_id
                    continue

                gtype = tds[1].text_content().strip()
                creator = tds[3].text_content().strip()
                players = tds[4].text_content().split()
                scores = tds[6].text_content().split()
                places = tds[7].text_content().split()
                deltas = tds[8].text_content().split()
                token = tds[9].xpath("div")[0].get("data-token")
                if not deltas:
                    # deltas = [None] * len(scores)
                    logger.debug("Game {} is not ready yet".format(players))
                    continue

                global_places = [self._places[un] for un in players]

                game = Game(game_id, token, gtype, players, scores, deltas, places, global_places)
                logger.debug("Adding game {}".format(game_id))
                games.append(game)
        except Exception:
            logger.info(traceback.format_exc())
            end_reached = True
        return end_reached, games
