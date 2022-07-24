import argparse
import logging
import shlex
import urllib
from datetime import datetime, timedelta, timezone
from functools import partial, wraps
from io import BytesIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackQueryHandler, ContextTypes, PrefixHandler

import allcups
import commands as cmd
import msg_formatter
import names

logger = logging.getLogger(__name__)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admins = await update.effective_chat.get_administrators()
    admins_ids = [admin.user['id'] for admin in admins]
    return update.effective_user.id in admins_ids


def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return update.effective_user.username in context.bot_data['bot_admins']


def private_chat_only(func):
    @wraps(func)
    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private':
            return None
        return func(update, context)

    return wrapper


def chat_and_bot_admins_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private' \
                and not is_bot_admin(update, context) \
                and not (await is_chat_admin(update, context)):
            return None
        return await func(update, context)

    return wrapper


def bot_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_bot_admin(update, context):
            return None
        return func(update, context)

    return wrapper


@chat_and_bot_admins_only
async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # reply_rows = ["🔥💬"]
    # reply_rows.append(f"/{cmd.SUBS[0]} - Список активных подписок")
    # reply_rows.append(f"/{cmd.SUB_TO[0]} nickname... - подписка на системные игры")
    # reply_rows.append(f"/{cmd.UNSUB_FROM[0]} nickname... - отписаться от системных игр")
    # reply_rows.append(f"/{cmd.UNSUB_FROM[0]} nickname... - отписаться от системных игр")
    # reply_rows.append("")

    # chat_settings = context.bot.chat_settings.get_settings(update.effective_chat.id)
    # reply_rows.append(f"Текущий чемпионат: `{chat_settings.current_cup.value}`")
    # reply_rows.append(f"/{cmd.POS[0]} [nickname...] - позиции участников")
    # reply_rows.append(f"/{cmd.TOP[0]} [N] - топ участников")

    await update.effective_message.reply_markdown("🔥")
    help_txt = """
Огненый привет!
Данный ботик пытается сделать участие в AI Cup'e снова удобным.

Все его команды начинуются на `/` или `!`.
Второй вариант чуть проще набирать, не переключая раскладки, и он не создает "тыкательных" ссылок в общих чатах (это опасно).
Многие команды имеют несколько форм. Например, данную инструкцию можно получить любой из команд:
`!start`, /help, `!help`, `!помощь`, `!хелб`, `!памаги`, `/рудз` и т.д.

Для многих действий, Кальциферу нужно знать какое соревнование и какая задача интересует чат:
`!contest CONTEST_SLUG`
где CONTEST\_SLUG - можно поискать в ссылках на сайте, например `coderoyale`.
Дальше набираем `!task` и выбираем задачу из списка. Ее можно менять по мере соревнования, чтобы всегда видеть актуальный лидерборд.
`!info` - пришлет текущую конфигурацию бота.

В *приватном* чате можно подписаться на свои системные игры - будут приходить результаты и ссылка на бой:
`!sub MY_CUPS_LOGIN`
MY\_CUPS\_LOGIN тут *регистрозависимый*.

Проверить рейтинг игроков:
`!pos CUPS_LOGIN...`
Можно указать один или несколько логинов. Они будут искаться как регистронезависимая подстрока.
`!pos ortid omka dema` - такой запрос сработает

Посмотреть топ:
`!top` или `!top 6`

Можно добавлять и удалять логины в список чата:
`!chat_add CUPS_LOGIN`
`!chat_remove CUPS_LOGIN`
CUPS\_LOGIN тут *регистрозависимый*.
И сравнивать результаты участников чата:
`!chat_top` или `!топ_чата`

Прислать график изменения рейтинга:
`!plot CUPS_LOGIN...`
CUPS\_LOGIN - *регистроНЕзависимый список логинов*
Можно отрисовать только рейтинг топов:
`!plot_top` или `!plot_top 6`
У команды есть `plotl` (l на конце) версия, для отрисовки линиями, а не сутпеньками.

Прислать ссылку на игру (без правильных ников):
`!game GAME_ID`
"""  # noqa
    await update.effective_message.reply_markdown(help_txt)


start = PrefixHandler(cmd.PREFIXES, cmd.HELP, _start)


@chat_and_bot_admins_only
async def _set_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if len(context.args) != 1:
        await update.effective_message.reply_text("🔥❓")
        return
    slug = context.args[0]

    contest = allcups.contest(slug)
    if contest is None:
        logger.warning(f"There is no contest with slug `{slug}`")
        await update.effective_message.reply_markdown(f"There is no c🔥ntest with slug `{slug}`")
        return

    context.chat_data['contest_slug'] = slug
    context.chat_data.pop('task_id', None)
    info_txt = msg_formatter.format_chat_info(contest, None)
    await update.effective_message.reply_markdown(info_txt)


set_contest = PrefixHandler(cmd.PREFIXES, cmd.CONTEST, _set_contest)


@chat_and_bot_admins_only
async def _info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contest = None
    task = None
    if 'contest_slug' in context.chat_data:
        contest = allcups.contest(context.chat_data['contest_slug'])
        if 'task_id' in context.chat_data:
            task = allcups.task(context.chat_data['task_id'])
    info_txt = msg_formatter.format_chat_info(contest, task)
    battle_login = context.chat_data.get('battle_login', None)
    if battle_login:
        info_txt += f"\nCUPS Battle Login: `{battle_login}`"

    await update.effective_message.reply_markdown(info_txt)


get_info = PrefixHandler(cmd.PREFIXES, cmd.INFO, _info)


async def _chat_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    cups_logins |= usernames
    context.chat_data['cups_logins'] = cups_logins

    msg_txt = msg_formatter.chat_logins(cups_logins)
    await update.effective_message.reply_markdown(msg_txt)


chat_add = PrefixHandler(cmd.PREFIXES, cmd.CHAT_ADD, _chat_add)


async def _chat_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    cups_logins.difference_update(usernames)
    context.chat_data['cups_logins'] = cups_logins

    msg_txt = msg_formatter.chat_logins(cups_logins)
    await update.effective_message.reply_markdown(msg_txt)


chat_remove = PrefixHandler(cmd.PREFIXES, cmd.CHAT_REMOVE, _chat_remove)


async def _chat_top(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    if not cups_logins:
        await update.effective_message.reply_markdown("Для чата не добавлены CUPS л🔥гины. "
                                                      f"Команда `!{cmd.CHAT_ADD[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])
    scores = [s for s in scores if s['user']['login'] in cups_logins]

    name = f"{task['contest']['name']}: {task['name']}"
    if short:
        text = msg_formatter.format_top(name, scores)
    else:
        text = msg_formatter.format_toop(name, scores)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.effective_message.reply_markdown(text)


chat_top = PrefixHandler(cmd.PREFIXES, cmd.CHAT_TOP, partial(_chat_top, short=True))
chat_toop = PrefixHandler(cmd.PREFIXES, cmd.CHAT_TOOP, partial(_chat_top, short=False))


async def _plot_logins(cups_logins,
                       update: Update,
                       context: ContextTypes.DEFAULT_TYPE,
                       relative_login=None,
                       plot_type='step') -> None:
    task = allcups.task(context.chat_data['task_id'])

    # context.bot_data.pop('history', None)
    history = context.bot_data.get('history', {})
    context.bot_data['history'] = history
    task_history = history.get(context.chat_data['task_id'], [])
    history[context.chat_data['task_id']] = task_history


    finish_date = datetime.fromisoformat(task['finish_date'])
    time_step = timedelta(minutes=15)
    now = datetime.now(timezone.utc)

    ts = datetime.fromisoformat(task['start_date'])
    end = min(finish_date, now)
    if task_history:
        ts = datetime.fromtimestamp(task_history[-1]['ts'], timezone.utc)

    # TODO: Remove in future.
    while ts > finish_date:
        task_history.pop()
        ts = datetime.fromtimestamp(task_history[-1]['ts'], timezone.utc)

    ts += time_step
    while ts <= end:
        scores = allcups.task_leaderboard(context.chat_data['task_id'], ts)
        lb = [{'rank': s['rank'], 'login': s['user']['login'], 'score': s['score']} for s in scores]
        task_history.append({
            'ts': ts.timestamp(),
            'leaderboard': lb
        })
        ts += time_step

    plt.clf()
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))

    # ax.tick_params(axis='x', rotation=0, labelsize=12)
    ax.tick_params(axis='y', rotation=0, labelsize=12, labelcolor='tab:red')
    myFmt = mdates.DateFormatter('%b %d %H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.grid(alpha=.9)
    time_limit = timedelta(days=2)
    plot_data = {}
    ls = set(cups_logins)
    if relative_login is not None:
        ls.add(relative_login)
    for login in ls:
        pd = []
        plot_data[login] = pd
        dates = []
        for h in task_history:
            d = datetime.fromtimestamp(h['ts'], timezone.utc)
            if now - d > time_limit:
                continue
            point = None
            for s in h['leaderboard']:
                if s['login'].lower() == login.lower():
                    point = s['score']
                    break
            pd.append(point)
            dates.append(d)

    if relative_login is not None and relative_login in plot_data:
        relative_data = list(plot_data[relative_login])
        for login in cups_logins:
            login_data = plot_data[login]
            for i, rel_d in enumerate(relative_data):
                if login_data[i] is None or rel_d is None:
                    login_data[i] = None
                else:
                    login_data[i] -= rel_d

        plt.axhline(y=0.0, color='darkviolet', linestyle='--', label=relative_login)

    for login in cups_logins:
        if relative_login is not None and login.lower() == relative_login.lower():
            continue
        if plot_type == 'lines':
            plt.plot(dates, plot_data[login], label=login)
        else:
            plt.step(dates, plot_data[login], where='mid', label=login)

    plt.grid(color='0.95')
    plt.legend(fontsize=16)

    plot_file = BytesIO()
    fig.tight_layout()
    fig.savefig(plot_file, format='png')
    plt.clf()
    plt.close(fig)
    plot_file.seek(0)

    await update.effective_message.reply_photo(plot_file, caption="🔥")


async def _plot_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, plot_type='step') -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    if not cups_logins:
        await update.effective_message.reply_markdown("Для чата не добавлены CUPS л🔥гины. "
                                                      f"Команда `!{cmd.CHAT_ADD[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    parser = ArgumentParser()
    parser.add_argument(
        '-r', '--relative', type=str, required=False,
        help='CUPS логин, относительно которого строить график'
    )
    args = shlex.split(update.effective_message.text)[1:]
    try:
        args = parser.parse_args(args)
    except argparse.ArgumentError as e:
        help = parser.format_help().split("\n")[0]
        help = help[help.find("[-h]") + 5:]
        msg = f"```\nUsage: {help}\n\n{e.message}\n```"
        logger.warning(msg)
        await update.effective_message.reply_markdown(msg)
        return

    await _plot_logins(cups_logins, update, context, plot_type=plot_type,
                       relative_login=args.relative)


plot_chat = PrefixHandler(cmd.PREFIXES, cmd.PLOT_CHAT, _plot_chat)
plotl_chat = PrefixHandler(cmd.PREFIXES, cmd.PLOTL_CHAT, partial(_plot_chat, plot_type="lines"))


async def _pos(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = set(login.lower() for login in context.args)
    if not cups_logins:
        await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])

    f_scores = []
    for s in scores:
        s_l = s['user']['login'].lower()
        for login in cups_logins:
            if login in s_l:
                f_scores.append(s)
    scores = f_scores

    if not scores:
        await update.effective_message.reply_text("Не  н🔥шел  таких  участник🔥в")
        return

    name = f"{task['contest']['name']}: {task['name']}"
    if short:
        text = msg_formatter.format_top(name, scores, header=False)
    else:
        text = msg_formatter.format_toop(name, scores, header=False)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.effective_message.reply_markdown(text)


pos = PrefixHandler(cmd.PREFIXES, cmd.POS, partial(_pos, short=True))
poss = PrefixHandler(cmd.PREFIXES, cmd.POOS, partial(_pos, short=False))


async def _top(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее соревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не выбрана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            logger.warning(f"Couldn't parse N for ai top callback: {context.args[0]}")
            await update.effective_message.reply_text("Ты меня ог🔥рчаешь")
            return
        if n == 0:
            await update.effective_message.reply_text("C🔥mmandos")
            return
        if n < 0:
            await update.effective_message.reply_text("Не н🔥до так")
            return

    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])[:n]
    name = f"{task['contest']['name']}: {task['name']}"

    horse_logins = context.application.chat_data[context.bot_data['horse_chat']].get('cups_logins',
                                                                                     set())
    is_horse_chat = context.bot_data['horse_chat'] == update.effective_chat.id
    # horse_logins = set()
    # if context.bot_data['horse_chat'] == update.effective_chat.id:
    #     horse_logins = context.chat_data.get('cups_logins', set())
    if short:
        text = msg_formatter.format_top(name, scores, horse_logins, is_horse_chat=is_horse_chat)
    else:
        text = msg_formatter.format_toop(name, scores)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.effective_message.reply_markdown(text)


top = PrefixHandler(cmd.PREFIXES, cmd.TOP, partial(_top, short=True))
toop = PrefixHandler(cmd.PREFIXES, cmd.TOOP, partial(_top, short=False))


@chat_and_bot_admins_only
async def _task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contest = None
    if 'contest_slug' in context.chat_data:
        contest = allcups.contest_navigation(context.chat_data['contest_slug'])['contest']

    if not contest:
        await update.effective_message.reply_markdown("Для данного чата не выбрано с🔥ревнование.")
        return
    keyboard = []
    for stage in contest['stages']:
        for r in stage['rounds']:
            for t in r['tasks']:
                name = f"{r['name']} :{t['name']}"
                data = f"task {t['id']}"
                keyboard.append([InlineKeyboardButton(name, callback_data=data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_markdown("Выберете задачу:", reply_markup=reply_markup)


@chat_and_bot_admins_only
async def _task_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    task_id = query.data.split()[1]
    task = allcups.task(task_id)
    contest = allcups.contest(task['contest']['slug'])
    context.chat_data['contest_slug'] = task['contest']['slug']
    context.chat_data['task_id'] = task_id

    info_txt = msg_formatter.format_chat_info(contest, task)
    await query.edit_message_text(info_txt, parse_mode='markdown')


set_task = PrefixHandler(cmd.PREFIXES, cmd.TASK, _task)
choose_task = CallbackQueryHandler(_task_button, pattern=r"^task (\d+)$")


@private_chat_only
async def _sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Укажи cups л🔥гин")
        return
    if len(context.args) > 1:
        await update.effective_message.reply_text("Подписаться можно только на 1 cups л🔥гин")
        return

    login = context.chat_data.pop('battle_login', None)
    if login:
        battle_subs = context.bot_data.get('battle_subs', dict())
        context.bot_data['battle_subs'] = battle_subs
        chats = battle_subs.get(login, set())
        battle_subs[login] = chats
        chats.discard(update.effective_chat.id)

    login = context.args[0]
    context.chat_data['battle_login'] = login
    battle_subs = context.bot_data.get('battle_subs', dict())
    context.bot_data['battle_subs'] = battle_subs
    chats = battle_subs.get('battle_subs', set())
    battle_subs[login] = chats
    chats.add(update.effective_chat.id)

    await update.effective_message.reply_markdown(
        f"Подписка на системные игры `{login}` установлена")


sub = PrefixHandler(cmd.PREFIXES, cmd.SUB_TO, _sub)


@private_chat_only
async def _unsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    login = context.chat_data.pop('battle_login', None)
    if login:
        battle_subs = context.bot_data.get('battle_subs', dict())
        context.bot_data['battle_subs'] = battle_subs
        chats = battle_subs.get(login, set())
        battle_subs[login] = chats
        chats.discard(update.effective_chat.id)
    await update.effective_message.reply_text("Подписка на системные игры отключена")


unsub = PrefixHandler(cmd.PREFIXES, cmd.UNSUB_FROM, _unsub)


# async def _sol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if 'contest_slug' not in context.chat_data:
#         await update.effective_message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
#                                             f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
#         return
#
#     if 'task_id' not in context.chat_data:
#         await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
#                                             f"Команда `!{cmd.TASK[0]}`")
#         return
#
#     if not context.args:
#         await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ник")
#         return
#
#     cups_login = context.args[0]
#
#     await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
#     solutions = allcups.task_solutions(context.chat_data['task_id'], cups_login)[:10]
#     text = msg_formatter.format_solutions(solutions)
#     if len(text) > 4000:
#         text = text[:-3][:4000] + ".🔥..🔥🔥```"
#     await update.effective_message.reply_markdown(text)
#
#
# solution_list = PrefixHandler(cmd.PREFIXES, cmd.SOLUTION_LIST, _sol)


async def _game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    if not context.args:
        await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ID  игры")
        return

    cups_login = context.args[0]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    task_battle = allcups.battles(context.chat_data['task_id'])[0]  # TODO: fix case with no battles

    replay_url = "https://cups.online" + task_battle['visualizer_url'] + "?"
    for _ in range(10):
        replay_url += "&player-names=" + urllib.parse.quote(names.get_name())
    #     replay_url += f"&client-ids=" + urllib.parse.quote(str(br['solution']['external_id']))
    replay_url += f"&replay=%2Fapi_v2%2Fbattles%2F{cups_login}%2Fget_result_file%2F"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text='Watch Replay', url=replay_url)]
    ])
    await update.effective_message.reply_markdown("🔥", reply_markup=reply_markup)


game = PrefixHandler(cmd.PREFIXES, cmd.GAME, _game)


async def _plot_logins(cups_logins,
                       update: Update,
                       context: ContextTypes.DEFAULT_TYPE,
                       relative_login=None,
                       relative_rank=None,
                       display_rank=False,
                       plot_type='step') -> None:
    task = allcups.task(context.chat_data['task_id'])
    display_field = 'rank' if display_rank else 'score'

    # context.bot_data.pop('history', None)
    history = context.bot_data.get('history', {})
    context.bot_data['history'] = history
    task_history = history.get(context.chat_data['task_id'], [])
    history[context.chat_data['task_id']] = task_history

    ts = datetime.fromisoformat(task['start_date'])
    finish_date = datetime.fromisoformat(task['finish_date'])
    time_step = timedelta(minutes=15)
    now = datetime.now(timezone.utc)
    end = min(finish_date, now)
    if task_history:
        ts = datetime.fromtimestamp(task_history[-1]['ts'], timezone.utc)

    # TODO: Remove in future.
    while ts > finish_date:
        task_history.pop()
        ts = datetime.fromtimestamp(task_history[-1]['ts'], timezone.utc)

    time_limit = timedelta(days=2)
    # ts = max(now - time_limit, ts)
    ts += time_step
    while ts <= end:
        scores = allcups.task_leaderboard(context.chat_data['task_id'], ts)
        lb = [{'rank': s['rank'], 'login': s['user']['login'], 'score': s['score']} for s in scores]
        task_history.append({
            'ts': ts.timestamp(),
            'leaderboard': lb
        })
        ts += time_step

    plt.clf()
    fig, ax = plt.subplots(1, 1, figsize=(15, 7))

    # ax.tick_params(axis='x', rotation=0, labelsize=12)
    ax.tick_params(axis='y', rotation=0, labelsize=12, labelcolor='tab:red')
    myFmt = mdates.DateFormatter('%b %d %H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.grid(alpha=.9)

    task_history = [h for h in task_history if now - datetime.fromtimestamp(h['ts'], timezone.utc) < time_limit]
    dates = [datetime.fromtimestamp(h['ts'], timezone.utc) for h in task_history]

    plot_data = {}
    ls = set(cups_logins)
    if relative_login is not None:
        ls.add(relative_login)

    for login in ls:
        pd = []
        plot_data[login] = pd
        for h in task_history:
            point = None
            for s in h['leaderboard']:
                if s['login'].lower() == login.lower():
                    point = s[display_field]
                    break
            pd.append(point)

    if relative_login is not None and relative_login in plot_data:
        relative_data = list(plot_data[relative_login])
        for login in cups_logins:
            login_data = plot_data[login]
            for i, rel_d in enumerate(relative_data):
                if login_data[i] is None or rel_d is None:
                    login_data[i] = None
                else:
                    login_data[i] -= rel_d

        plt.axhline(y=0.0, color='darkviolet', linestyle='--', label=relative_login)

    if relative_rank is not None:
        relative_data = [
            h['leaderboard'][relative_rank - 1][display_field] if relative_rank <= len(h['leaderboard']) else None
            for h in task_history
        ]
        for login in cups_logins:
            login_data = plot_data[login]
            for i, rel_d in enumerate(relative_data):
                if login_data[i] is None or rel_d is None:
                    login_data[i] = None
                else:
                    login_data[i] -= rel_d

        plt.axhline(y=0.0, color='darkviolet', linestyle='--', label=f'rank={relative_rank}')

    for login in cups_logins:
        if relative_login is not None and login.lower() == relative_login.lower():
            continue
        if plot_type == 'lines':
            plt.plot(dates, plot_data[login], label=login)
        else:
            plt.step(dates, plot_data[login], where='mid', label=login)

    plt.grid(color='0.95')
    plt.legend(fontsize=16, bbox_to_anchor=(1, 1), loc="upper left")

    if display_field == 'rank':
        plt.gca().invert_yaxis()

    plot_file = BytesIO()
    fig.tight_layout()
    fig.savefig(plot_file, format='png')
    plt.clf()
    plt.close(fig)
    plot_file.seek(0)

    await update.effective_message.reply_photo(plot_file, caption="🔥")


async def _plot(update: Update, context: ContextTypes.DEFAULT_TYPE, plot_type='step') -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    parser = ArgumentParser()
    parser.add_argument(
        '-r', '--relative', type=str, required=False,
        help='CUPS логин, относительно которого строить график'
    )
    parser.add_argument(
        '-rr', '--relative-rank', type=int, required=False,
        help='Место, относительно которого строить график'
    )
    parser.add_argument(
        '-dr', '--display-rank', action='store_true',
        help='График мест'
    )
    parser.add_argument("cups_logins", type=str, nargs="+",
                        help='CUPS логины для отрисовки на графике')

    args = shlex.split(update.effective_message.text)[1:]
    try:
        args = parser.parse_args(args)
        if args.relative is not None and args.relative_rank is not None:
            parser.error('Use one of -r and -rr options')
    except argparse.ArgumentError as e:
        help = parser.format_help().split("\n")[0]
        help = help[help.find("[-h]") + 5:]
        msg = f"```\nUsage: {help}\n\n{e.message}\n```"
        logger.warning(msg)
        await update.effective_message.reply_markdown(msg)
        return

    await _plot_logins(args.cups_logins, update, context, plot_type=plot_type,
                       relative_login=args.relative, relative_rank=args.relative_rank, display_rank=args.display_rank)


plot = PrefixHandler(cmd.PREFIXES, cmd.PLOT, _plot)
plotl = PrefixHandler(cmd.PREFIXES, cmd.PLOTL, partial(_plot, plot_type="lines"))


async def _plot_top(update: Update, context: ContextTypes.DEFAULT_TYPE, plot_type='step') -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    parser = ArgumentParser()
    parser.add_argument(
        '-r', '--relative', type=str, required=False,
        help='CUPS логин, относительно которого строить график'
    )
    parser.add_argument(
        '-rr', '--relative-rank', type=int, required=False,
        help='Место, относительно которого строить график'
    )
    parser.add_argument(
        '-dr', '--display-rank', action='store_true',
        help='График мест'
    )

    def positive_int(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError("%s - это слишк🔥м мало" % value)
        return ivalue

    parser.add_argument("N", type=positive_int, default=10, nargs='?',
                        help='Количество участников из топа')

    args = shlex.split(update.effective_message.text)[1:]
    try:
        args = parser.parse_args(args)
        if args.relative is not None and args.relative_rank is not None:
            parser.error('Use one of -r and -rr options')
    except argparse.ArgumentError as e:
        help = parser.format_help().split("\n")[0]
        help = help[help.find("[-h]") + 5:]
        msg = f"```\nUsage: {help}\n\n{e.message}\n```"
        logger.warning(msg)
        await update.effective_message.reply_markdown(msg)
        return

    scores = allcups.task_leaderboard(context.chat_data['task_id'])[:args.N]
    logins = [s['user']['login'] for s in scores]

    await _plot_logins(logins, update, context, plot_type=plot_type,
                       relative_login=args.relative, relative_rank=args.relative_rank, display_rank=args.display_rank)


plot_top = PrefixHandler(cmd.PREFIXES, cmd.PLOT_TOP, _plot_top)
plotl_top = PrefixHandler(cmd.PREFIXES, cmd.PLOTL_TOP, partial(_plot_top, plot_type="lines"))


async def _games(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.effective_message.reply_markdown(
            "Для чата не установлено текущее с🔥ревнование. "
            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.effective_message.reply_markdown("Для чата не в🔥брана задача. "
                                                      f"Команда `!{cmd.TASK[0]}`")
        return

    if not context.args:
        await update.effective_message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return
    cups_login = context.args[0]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    task = allcups.task(context.chat_data['task_id'])
    battles = allcups.battles(context.chat_data['task_id'],
                              max_count=10,
                              search=cups_login.lower())[:10]

    if not battles:
        await update.effective_message.reply_text("Не  н🔥шел  таких  участник🔥в")
        return

    name = f"{task['contest']['name']}: {task['name']}"
    text = msg_formatter.format_battles(name, cups_login, battles)
    await update.effective_message.reply_markdown(text)


games = PrefixHandler(cmd.PREFIXES, cmd.GAMES, _games)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Error: "%s" update: %s' % (context.error, update))
    if update:
        await update.effective_message.reply_text(f"Во мне что-то сл🔥малось: {context.error}")
