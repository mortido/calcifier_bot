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
    rows.append("    PLAYER           LANGUAGE  W.R. SCORE")
    rows.append("-----------------------------------------")
    for i, player in enumerate(players):
        rows.append("{}{}{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 16).ljust(17),
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
    rows.append("    PLAYER   SCORE")
    rows.append("------------------")
    for i, player in enumerate(players):
        rows.append("{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 7).ljust(7),
            player.score.rjust(6)
        ))
    rows.append("```")
    return "\n".join(rows)


def format_poos(chart_name, players):
    rows = ["```"]
    for i, player in players:
        rows.append("{}{}{}{}{}".format(
            str(i + 1).ljust(4),
            trim_len(player.username, 16).ljust(17),
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
            trim_len(player.username, 7).ljust(7),
            player.score.rjust(6)
        ))
    rows.append("```")
    return "\n".join(rows)


def format_game(game: Game):
    rows = [f"http://russianaicup.ru/game/view/{game.gid}"]
    rows.append("```")
    rows.append(f"{game.gtype.ljust(10)}           SCORE   Δ")
    for i in range(len(game.scores)):
        rows.append("{}{}{}{}".format(
            game.places[i].ljust(3),
            trim_len(game.players[i], 16).ljust(17),
            game.scores[i].rjust(6),
            game.deltas[i].rjust(4)
        ))
    rows.append("```")
    return "\n".join(rows)
