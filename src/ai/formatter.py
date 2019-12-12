from typing import List
from ai.chart import Player, Game


def format_topic(topic):
    first_link = None
    ts = 0
    for message in topic.messages.values():
        if first_link is None or ts > message.pub_timestamp:
            ts = message.pub_timestamp
            first_link = message.link
    return f"- [{topic.title}]({first_link}) ({len(topic.messages)})"


def format_category(category, topics):
    return f'**{category}:**\n' + \
           '\n'.join(format_topic(topic) for topic in topics if topic.category == category)


def format_forum_updates(topics):
    categories = sorted(set(topic.category for topic in topics))
    result = []
    for category in categories:
        result.append(format_category(category, topics))
    return '\n\n'.join(result)


def trim_len(string, max_len):
    return string if len(string) <= max_len else string[:max_len - 1] + "…"


def format_toop(chart_name, players: List[Player]):
    rows = ["```"]
    rows.append(chart_name.upper())
    rows.append("")
    rows.append("    PLAYER          LANGUAGE  W.R. SCORE")
    rows.append("----------------------------------------")
    for i, player in enumerate(players):
        rows.append("{}{}{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 16).ljust(16),
            player.language.ljust(9),
            player.winrate.rjust(5),
            player.score.rjust(6)
        ))
    rows.append("```")
    return "\n".join(rows)


def format_top(chart_name, players: List[Player]):
    rows = ["```"]
    rows.append(chart_name.upper())
    rows.append("")
    rows.append("    PLAYER     SCORE")
    rows.append("--------------------")
    for i, player in enumerate(players):
        rows.append("{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 11).ljust(11),
            player.score.rjust(5)
        ))
    rows.append("```")
    return "\n".join(rows)


def format_poos(chart_name, players):
    rows = ["```"]
    for i, player in players:
        rows.append("{}{}{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 16).ljust(16),
            player.language.ljust(9),
            player.winrate.rjust(5),
            player.score.rjust(6)
        ))
    rows.append("```")
    return "\n".join(rows)


def format_pos(chart_name, players):
    rows = ["```"]
    for i, player in players:
        rows.append("{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 11).ljust(11),
            player.score.rjust(5)
        ))
    rows.append("```")
    return "\n".join(rows)


import random

win_phrases = [
    "Ты на правильном пути",
    "Ты идешь хорошо",
    "Это реальный прогресс",
    "Ты хорошо поработал",
    "Улыбнись!",
    "Вот это да!",
    "Нифига себе!",
    "🔥🔥🔥",
    "Так держать!",
    "Продолжай в том же духе!",
    "mortido может лучше",
    "Не зазнавайся",
    "Ты можешь еще лучше!",
    "Как ты хорош!",
    "Как сильны твои лапищи!",
    "Ты на правильном пути",
    "Бах! Тыщ! Бум!"
]

loose_phrases = [
    "Бывает и хуже",
    "Слезами горю не поможешь",
    "На этой игре свет клином не сошелся",
    "Зато ты веселый",
    "Твоя мама тебя любит",
    "Противнику просто повезло",
    "Ты проиграл битву, но не проиграл войну",
    "Это не конец света",
    "Commandos тоже терпел поражения",
    "Нет худа без добра",
    "Не сдавайся!",
    "Давай, ты можешь!",
    "Выше голову!",
    "Не вешай нос!",
    "Не унывай!",
    "Не... ну это совсем хреновая игра...",
]


def format_game(game: Game, win):
    rows = [random.choice(win_phrases if win else loose_phrases),
            f"http://russianaicup.ru/game/view/{game.gid}",
            "```",
            f"{game.gtype.ljust(10)}          SCORE    Δ  LB"]
    for i in range(len(game.scores)):
        rows.append("{}{}{}{}{}".format(
            game.places[i].ljust(3),
            trim_len(game.players[i], 16).ljust(16),
            game.scores[i].rjust(6),
            game.deltas[i].rjust(5),
            game.global_places[i].rjust(4)
        ))
    rows.append("```")
    return "\n".join(rows)
