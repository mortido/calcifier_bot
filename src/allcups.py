from datetime import datetime, timedelta, timezone

import cachetools.func
import requests

ALLCUPS_API_URL = "https://cups.online/api_v2/"


# TRACKS = ["ai", "ml", "sport_coding", "design", "highload"]


def tracks():
    url = ALLCUPS_API_URL + "categories"
    response = requests.get(url, timeout=10)
    return response.json()


def _get_all_pages(*args, **kwargs):
    json_response = requests.get(*args, timeout=10, **kwargs).json()
    result = json_response['results']
    while json_response['next']:
        response = requests.get(json_response['next'], timeout=10)
        json_response = response.json()
        result = result + json_response['results']
    return result


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def contests(track=None):
    params = {}
    if track:
        params['category'] = track
    url = ALLCUPS_API_URL + "contests"
    return _get_all_pages(url, params=params)


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def contest_navigation(slug):
    url = ALLCUPS_API_URL + f"contests/{slug}/navigation"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def contest(slug):
    url = ALLCUPS_API_URL + f"contests/{slug}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def round(id):
    url = ALLCUPS_API_URL + f"round/{id}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def task(id):
    url = ALLCUPS_API_URL + f"task/{id}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return None
    return response.json()


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def battles_bot(task_id, since=None):
    url = ALLCUPS_API_URL
    url += f"battles/task/{task_id}/bot/"
    params = {}
    since = since + timedelta(hours=3)
    if since is not None:
        # params["since"] = since.isoformat().replace("+00:00", "Z")
        params["since"] = since.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    response = requests.get(url, params=params, timeout=10)
    json_response = response.json()
    return json_response['battles']


@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def battles(task_id=None, max_count=1000, search=None):  # , last_battle_id=None):
    url = ALLCUPS_API_URL
    if task_id:
        url += f"battles/task/{task_id}"
        params = {"page_size": 108}
        if search:
            params["search"] = search
        response = requests.get(url, params=params, timeout=10)
        json_response = response.json()
        # if 'results' not in json_response:
        #     return []
        results = json_response['results']
        while 'next' in json_response and json_response['next'] and len(results) < max_count:
            response = requests.get(json_response['next'], timeout=10)
            json_response = response.json()
            results = results + json_response['results']

        return results
        # return _get_all_pages(url, params=params)
    else:
        url += "contests/battles"
        params = {"page_size": 120}
        return _get_all_pages(url, params=params)


# TASK LEADER BOARD
# ROUND LEADER BOARD
# https://cups.online/api_v2/task/1058/leaderboard/?page_size=108

@cachetools.func.ttl_cache(maxsize=128, ttl=10)
def task_leaderboard(task_id, date=None):
    url = ALLCUPS_API_URL + f"task/{task_id}/leaderboard/"
    if date is None:
        date = datetime.now(timezone.utc)
    else:
        date -= timedelta(days=1)
    params = {
        "page_size": 1000,
        "date": date.isoformat()
    }
    return _get_all_pages(url, params=params)

# https://cups.online/api_v2/task/1314/users_search/?page_size=120

# @cachetools.func.ttl_cache(maxsize=128, ttl=10)
# def task_solutions(task_id, login):
#     url = ALLCUPS_API_URL + f"task/{task_id}/solutions_search"
#     params = {
#         "page_size": 120,
#         "login": login
#     }
#     cookies = {'csrftoken': '-',
#                'sessionid': '-'}
#     # return _get_all_pages(url, params=params)
#     response = requests.get(url, params=params, cookies=cookies)
#     return response.json()['results']
