import requests
import cachetools.func

ALLCUPS_API_URL = "https://cups.online/api_v2/"

# TRACKS = ["ai", "ml", "sport_coding", "design", "highload"]


def tracks():
    url = ALLCUPS_API_URL + "categories"
    response = requests.get(url)
    return response.json()


def _get_all_pages(*args, **kwargs):
        json_response = requests.get(*args, **kwargs).json()
        result = json_response['results']
        while json_response['next']:
            response = requests.get(json_response['next'])
            json_response = response.json()
            result = result + json_response['results']
        return result


def contests(track=None):
    params = {}
    if track:
        params['category'] = track
    url = ALLCUPS_API_URL + "contests"
    return _get_all_pages(url, params=params)

def contest_navigation(slug):
    url = ALLCUPS_API_URL + f"contests/{slug}/navigation"
    response = requests.get(url)
    return response.json()

def contest_short(slug):
    url = ALLCUPS_API_URL + f"contests/{slug}/short"
    response = requests.get(url)
    return response.json()

def round(id):
    url = ALLCUPS_API_URL + f"round/{id}"
    response = requests.get(url)
    return response.json()

# TASK LEADER BOARD
# ROUND LEADER BOARD
# https://cups.online/api_v2/task/1058/leaderboard/?page_size=108

@cachetools.func.ttl_cache(maxsize=128, ttl=20)
def task_leaderboard(task_id):
    url = ALLCUPS_API_URL + f"task/{task_id}/leaderboard"
    params = {"page_size": 108}
    return _get_all_pages(url, params=params)
