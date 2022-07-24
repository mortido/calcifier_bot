from datetime import datetime, timezone
import urllib.parse
import random
import pytz


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


def format_top(chart_name, scores, horse_logins=None, header=True):
    if horse_logins is None:
        horse_logins = set()
    rows = ["```"]
    if header:
        rows.append(chart_name.upper())
        rows.append("")
        rows.append("    PLAYER     SCORE")
        rows.append("--------------------")
    for score in scores:
        login = trim_len(score['user']['login'], 10)
        rows.append("{}{}{}".format(
            str(score['rank']).ljust(4),
            login.ljust(11),
            "{:.3f}".format(score['score']).rjust(5)
        ))
        if score['user']['login'] in horse_logins:
            rows[-1] += " 🐴"
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
    "Я бы и сам поучаствовал, но до твоего бота мне далеко.",
    "Жги, грабь, доминируй!",
    "Держи `1u + pos.x + width_ * (1u + pos.y)` - это кусок кода mortido, он приносит segfault'ы",
    "А ты любишь лошадей?",
    "Игого!",
    "Ты заслужил чашечку чая",
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
    "Вообще сейчас есть много севрвисов психологической помощи онлайн.",
    "Не... ну это совсем хреновая игра...",
    "Мы его запомним и отомстим",
    "Давай что-нибудь сожжем?",
    "Пожалуйста... Ну и не нужно...",
    "Держи `for (auto &entity : workers){` - это кусок кода Commandos'a, он приносит удачу",
    "У всех бывают осечки.",
    "Хорошо, когда есть, к чему стремиться.",
    "Каждое поражение делает тебя сильнее.",
    "Кажется, нужна ещё пара ифов...",
    "Хм... посмотришь, почему так вышло?",
    "Попробуй сменить язык",
    "Лучше быть последним — первым, чем первым — последним",
    "Легко вставать, когда ты не ложился.",
    "Иногда жизнь — это жизнь, а ты в ней иногда.",
    "Лучше один раз упасть, чем сто раз упасть.",
    "Если ты не видишь, значит ты слепой.",
    "Запомни, а то забудешь.",
    "Будь сильным.",
    "Проиграть - это как победить, только програть.",
    "Зато ты лучше их в чем-то другом, но это не точно.",
    "Это какое-то говно",
    "Давай так больше не делать.",
    "Предлагаю откатить последнее изменение.",
    "Нафиг эти сложности, просто напиши несколько if'ов",
    "Кем бы ты ни был, кем бы ты не стал, помни, где ты был и кем ты стал.",
    "Делай как надо, как не надо не делай.",
    "Держи [ссылку](https://github.com/core2duo/RHC-AI)"
]


def format_battles(name, cups_login, battles):
    cups_login = cups_login.lower()
    rows = []
    for battle in battles:
        replay_url = "https://cups.online" + battle['visualizer_url'] + "?"
        for br in battle['battle_results']:
            replay_url += f"&player-names=" + urllib.parse.quote(br['user']['login'])
            replay_url += f"&client-ids=" + urllib.parse.quote(str(br['solution']['external_id']))
        replay_url += f"&replay=" + urllib.parse.quote(battle['battle_result_file'])
        rows.append(f"Game: ` {battle['id']}".ljust(25) + f"` [REPLAY]({replay_url})")
        created_at = datetime.fromisoformat(battle['created_at'])
        created_at = created_at.astimezone(pytz.timezone("Europe/Moscow"))
        rows.append(f"Created:  `{created_at.strftime('%m/%d/%Y %H:%M:%S MSK')}`")
        rows.append("```")
        scores = sorted(battle['battle_results'], key=lambda x: x['score'], reverse=True)
        for s in scores:
            login = s['user']['login']
            if cups_login in s['user']['login'].lower():
                login = "* " + login

            rows.append("{}[{}]{}".format(
                trim_len(login, 15).ljust(16),
                s['solution']['id'],
                str(int(s['score'])).rjust(6)
            ))

        rows.append("```")
        rows.append("")

    return "\n".join(rows)


def format_game(battle, name, scores, my_lb, win_flag, solution):
    # win = int(game.deltas[player_idx]) > 0
    # rows = [random.choice(win_phrases if win else loose_phrases),
    #         f"http://russianaicup.ru/game/view/{game.gid}",
    # Δ
    game_type = "🏆 RANKED" if battle['is_ranked'] else "🤡 CUSTOM"
    rows = [
        # f"{name.ljust(30)}     SCORE    Δ   LB"]
        f"`{name.ljust(30)}`",
        f"Game:  `{battle['id']}  {game_type}`",
        f"SOLUTION ID:  `{solution}`",
        "LB:  `{}`   Score:  `{:.3f}`".format(my_lb['rank'], my_lb['score']),
        "",
        "```",
    ]

    my_login = ""
    all_logins = {}
    for s in scores:
        login = "* " + s['login'] if s['sub_flag'] else s['login']
        if s['sub_flag']:
            my_login = s['login']
        all_logins[s['login']] = max(all_logins.get(s['login'], 0), s['score'])
        rows.append("[{}] {}{}{}".format(
            str(s['lb_rank']).rjust(3),
            trim_len(login, 10).ljust(11),
            trim_len(s['language'], 7).ljust(8),
            str(int(s['score'])).rjust(6)
        ))
    rows.append("```")

    rows.append(random.choice(win_phrases) if win_flag else random.choice(loose_phrases))
    return "\n".join(rows)
