from datetime import datetime, timezone


def trim_len(string, max_len):
    return string if len(string) <= max_len else string[:max_len - 1] + "…"


# def format_toop(chart_name, players):
#     rows = ["```"]
#     rows.append(chart_name.upper())
#     rows.append("")
#     rows.append("    PLAYER          LANGUAGE  W.R. SCORE")
#     rows.append("----------------------------------------")
#     for i, player in enumerate(players):
#         rows.append("{}{}{}{}{}".format(
#             str(i + 1).ljust(4),
#             trim_len(player.username, 16).ljust(16),
#             player.language.ljust(9),
#             player.winrate.rjust(5),
#             player.score.rjust(6)
#         ))
#     rows.append("```")
#     return "\n".join(rows)


def format_top(chart_name, scores):
    rows = ["```"]
    rows.append(chart_name.upper())
    rows.append("")
    rows.append("    PLAYER     SCORE")
    rows.append("--------------------")
    for score in scores:
        rows.append("{}{}{}".format(
            str(score['rank']).ljust(4),
            trim_len(score['user']['login'], 10).ljust(11),
            "{:.3f}".format(score['score']).rjust(5)
        ))
    rows.append("```")
    return "\n".join(rows)


# def format_poos(chart_name, players):
#     rows = ["```"]
#     for i, player in players:
#         rows.append("{}{}{}{}{}".format(
#             str(i + 1).ljust(4),
#             trim_len(player.username, 16).ljust(16),
#             player.language.ljust(9),
#             player.winrate.rjust(5),
#             player.score.rjust(6)
#         ))
#     rows.append("```")
#     return "\n".join(rows)


def chat_logins(logins):
    msg = "CUPS Логины чата: `"
    if logins:
        msg += ", ".join(sorted(logins))
    else:
        msg += "СПИСОК ПУСТ"
    msg += "`"
    return msg


# def format_pos(chart_name, players):
#     rows = ["```"]
#     for i, player in players:
#         rows.append("{}{}{}".format(
#             str(i + 1).ljust(4),
#             trim_len(player.username, 11).ljust(11),
#             player.score.rjust(5)
#         ))
#     rows.append("```")
#     return "\n".join(rows)


# def format_solutions(solutions):
#     rows = ["```"]
#     for sol in solutions:
#         t=0
#         # rows.append("{}{}{}".format(
#         #     str(i + 1).ljust(4),
#         #     trim_len(player.username, 11).ljust(11),
#         #     player.score.rjust(5)
#         # ))
#     rows.append("```")
#     return "\n".join(rows)


def td2s(td):
    return str(td).split(".")[0]


def format_chat_info(contest=None, task=None) -> str:
    lines = []
    if contest:
        lines.append(f"Соревнование: `{contest['name']}`")

        now = datetime.now(timezone.utc)
        start_date = datetime.fromisoformat(contest['start_date'])
        end_date = datetime.fromisoformat(contest['finish_date'])
        if start_date > now:
            lines.append(f"Начнется через: `{td2s(start_date - now)}`")
        elif end_date > now:
            lines.append(f"Закончится через: `{td2s(end_date - now)}`")
        else:
            lines.append("`Соревнование закончилось.`")

        lines.append("")
        cround = None
        for r in contest['round_set']:
            start_date = datetime.fromisoformat(r['start_date'])
            end_date = datetime.fromisoformat(r['finish_date'])
            if end_date > now:
                cround = r
                break
        if cround:
            lines.append(f"Раунд: `{cround['name']}`")
            if start_date > now:
                lines.append(f"Начнется через: `{td2s(start_date - now)}`")
            else:
                lines.append(f"Закончится через: `{td2s(end_date - now)}`")
            lines.append("")

        if task:
            lines.append(f"Задача: `{task['name']}`")
        else:
            lines.append(f"Задача: `НЕ ВЫБРАНА, ЛИДЕРБОРД НЕДОСТУПЕН`")
    else:
        lines.append("Соревнование: `НЕ ВЫБРАНО`")
    return '\n'.join(lines)


import random

win_phrases = [
    "Ты на правильном пути",
    "Ты идешь хорошо",
    "Это реальный прогрес",
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
    "Бах! Тыщ! Бум!",
    "Кажется, ты идёшь к победе!",
    "У тебя здорово получается!",
    "Чем выше поднимаешься - тем больнее падать.",
    "Интересно, это заслуженная победа, или просто повезло?",
    "Уверенно.",
    "Like a boss.",
    "Держи `1u + pos.x + width_ * (1u + pos.y)` - это кусок кода mortido, он приносит segfault'ы",
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
    "Мы его запомним и отомстим",
    "Пожалуйста... Ну и не нужно...",
    "Держи `for (auto &entity : workers){` - это кусок кода Commandos'a, он приносит удачу",
    "У всех бывают осечки.",
    "Хорошо, когда есть, к чему стремиться.",
    "Каждое поражение делает тебя сильнее.",
    "Кажется, нужна ещё пара ифов...",
    "Хм... посмотришь, почему так вышло?",
    "Попробуй сменить язык",
]


def format_game(battle, name, scores, my_lb):
    # win = int(game.deltas[player_idx]) > 0
    # rows = [random.choice(win_phrases if win else loose_phrases),
    #         f"http://russianaicup.ru/game/view/{game.gid}",
    # Δ
    rows = [
            # f"{name.ljust(30)}     SCORE    Δ   LB"]
            f"`{name.ljust(30)}`",
            f"Game ID:  `{battle['id']}`",
            "LB:  `{}`   Score:  `{:.3f}`".format(my_lb['rank'], my_lb['score']),
            "",
            "```",
            ]

    for s in scores:
        login = "* " + s['login'] if s['sub_flag'] else s['login']
        rows.append("[{}] {}{}{}".format(
            str(s['lb_rank']).rjust(3),
            trim_len(login, 10).ljust(11),
            trim_len(s['language'], 7).ljust(8),
            str(int(s['score'])).rjust(6)
        ))
    rows.append("```")
    return "\n".join(rows)
