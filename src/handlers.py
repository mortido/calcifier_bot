from functools import wraps, partial
import logging
import urllib
from io import BytesIO
from datetime import datetime, timezone, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import PrefixHandler, ContextTypes, CallbackQueryHandler

import commands as cmd
import msg_formatter
import allcups
import names

logger = logging.getLogger(__name__)


def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admins = update.effective_chat.get_administrators()
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
    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private' \
                and not is_bot_admin(update, context) \
                and not is_chat_admin(update, context):
            return None
        return func(update, context)

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
    reply_rows = ["🔥💬"]
    # reply_rows.append(f"/{cmd.SUBS[0]} - Список активных подписок")
    # reply_rows.append(f"/{cmd.SUB_TO[0]} nickname... - подписка на системные игры")
    # reply_rows.append(f"/{cmd.UNSUB_FROM[0]} nickname... - отписаться от системных игр")
    # reply_rows.append(f"/{cmd.UNSUB_FROM[0]} nickname... - отписаться от системных игр")
    # reply_rows.append("")

    # chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
    # reply_rows.append(f"Текущий чемпионат: `{chat_settings.current_cup.value}`")
    # reply_rows.append(f"/{cmd.POS[0]} [nickname...] - позиции участников")
    reply_rows.append(f"/{cmd.TOP[0]} [N] - топ участников")

    await update.message.reply_markdown("\n".join(reply_rows))


start = PrefixHandler(cmd.PREFIXES, cmd.HELP, _start)


@chat_and_bot_admins_only
async def _set_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    if len(context.args) != 1:
        await update.message.reply_text("🔥❓")
        return
    slug = context.args[0]

    contest = allcups.contest(slug)
    if contest is None:
        logger.warning(f"There is no contest with slug `{slug}`")
        await update.message.reply_markdown(f"There is no c🔥ntest with slug `{slug}`")
        return

    context.chat_data['contest_slug'] = slug
    context.chat_data.pop('task_id', None)
    info_txt = msg_formatter.format_chat_info(contest, None)
    await update.message.reply_markdown(info_txt)


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

    await update.message.reply_markdown(info_txt)


get_info = PrefixHandler(cmd.PREFIXES, cmd.INFO, _info)


async def _chat_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    cups_logins |= usernames
    context.chat_data['cups_logins'] = cups_logins

    msg_txt = msg_formatter.chat_logins(cups_logins)
    await update.message.reply_markdown(msg_txt)


chat_add = PrefixHandler(cmd.PREFIXES, cmd.CHAT_ADD, _chat_add)


async def _chat_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    cups_logins.difference_update(usernames)
    context.chat_data['cups_logins'] = cups_logins

    msg_txt = msg_formatter.chat_logins(cups_logins)
    await update.message.reply_markdown(msg_txt)


chat_remove = PrefixHandler(cmd.PREFIXES, cmd.CHAT_REMOVE, _chat_remove)


async def _chat_top(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не в🔥брана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = context.chat_data.get('cups_logins', set())
    if not cups_logins:
        await update.message.reply_markdown("Для чата не добавлены CUPS л🔥гины. "
                                            f"Команда `!{cmd.CHAT_ADD[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
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
    await update.message.reply_markdown(text)


chat_top = PrefixHandler(cmd.PREFIXES, cmd.CHAT_TOP, partial(_chat_top, short=True))
chat_toop = PrefixHandler(cmd.PREFIXES, cmd.CHAT_TOOP, partial(_chat_top, short=False))


async def _pos(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не в🔥брана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = set(l.lower() for l in context.args)
    if not cups_logins:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])

    f_scores = []
    for s in scores:
        s_l = s['user']['login'].lower()
        for l in cups_logins:
            if l in s_l:
                f_scores.append(s)
    scores = f_scores

    if not scores:
        await update.message.reply_text("Не  н🔥шел  таких  участник🔥в")
        return

    name = f"{task['contest']['name']}: {task['name']}"
    if short:
        text = msg_formatter.format_top(name, scores)
    else:
        text = msg_formatter.format_toop(name, scores)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.message.reply_markdown(text)


pos = PrefixHandler(cmd.PREFIXES, cmd.POS, partial(_pos, short=True))
poss = PrefixHandler(cmd.PREFIXES, cmd.POOS, partial(_pos, short=False))


async def _top(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее соревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не выбрана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            logger.warning(f"Couldn't parse N for ai top callback: {context.args[0]}")
            await update.message.reply_text("Ты меня ог🔥рчаешь")
            return
        if n == 0:
            await update.message.reply_text("C🔥mmandos")
            return
        if n < 0:
            await update.message.reply_text("Не н🔥до так")
            return

    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])[:n]
    name = f"{task['contest']['name']}: {task['name']}"
    if short:
        text = msg_formatter.format_top(name, scores)
    else:
        text = msg_formatter.format_toop(name, scores)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.message.reply_markdown(text)


top = PrefixHandler(cmd.PREFIXES, cmd.TOP, partial(_top, short=True))
toop = PrefixHandler(cmd.PREFIXES, cmd.TOOP, partial(_top, short=False))


@chat_and_bot_admins_only
async def _task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contest = None
    if 'contest_slug' in context.chat_data:
        contest = allcups.contest_navigation(context.chat_data['contest_slug'])['contest']

    if not contest:
        await update.message.reply_markdown("Для данного чата не выбрано с🔥ревнование.")
        return
    keyboard = []
    for stage in contest['stages']:
        for r in stage['rounds']:
            for t in r['tasks']:
                name = f"{r['name']} :{t['name']}"
                data = f"task {t['id']}"
                keyboard.append([InlineKeyboardButton(name, callback_data=data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_markdown("Выберете задачу:", reply_markup=reply_markup)


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
choose_task = CallbackQueryHandler(_task_button, pattern="^task (\d+)$")


@private_chat_only
async def _sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажи cups л🔥гин")
        return
    if len(context.args) > 1:
        await update.message.reply_text("Подписаться можно только на 1 cups л🔥гин")
        return
    login = context.args[0]
    context.chat_data['battle_login'] = login
    battle_subs = context.bot_data.get('battle_subs', dict())
    context.bot_data['battle_subs'] = battle_subs
    chats = battle_subs.get('battle_subs', set())
    battle_subs[login] = chats
    chats.add(update.effective_chat.id)

    await update.message.reply_markdown(f"Подписка на системные игры `{login}` установлена")


sub = PrefixHandler(cmd.PREFIXES, cmd.SUB_TO, _sub)


@private_chat_only
async def _unsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    login = context.chat_data.pop('battle_login', None)
    if login:
        battle_subs = context.bot_data.get('battle_subs', dict())
        context.bot_data['battle_subs'] = battle_subs
        chats = battle_subs.get('battle_subs', set())
        battle_subs[login] = chats
        chats.discard(update.effective_chat.id)
    await update.message.reply_text("Подписка на системные игры отключена")


unsub = PrefixHandler(cmd.PREFIXES, cmd.UNSUB_FROM, _unsub)


# async def _sol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if 'contest_slug' not in context.chat_data:
#         await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
#                                             f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
#         return
#
#     if 'task_id' not in context.chat_data:
#         await update.message.reply_markdown("Для чата не в🔥брана задача. "
#                                             f"Команда `!{cmd.TASK[0]}`")
#         return
#
#     if not context.args:
#         await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
#         return
#
#     cups_login = context.args[0]
#
#     await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
#     solutions = allcups.task_solutions(context.chat_data['task_id'], cups_login)[:10]
#     text = msg_formatter.format_solutions(solutions)
#     if len(text) > 4000:
#         text = text[:-3][:4000] + ".🔥..🔥🔥```"
#     await update.message.reply_markdown(text)
#
#
# solution_list = PrefixHandler(cmd.PREFIXES, cmd.SOLUTION_LIST, _sol)


async def _game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не в🔥брана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    if not context.args:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ID  игры")
        return

    cups_login = context.args[0]

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    task_battle = allcups.battles(context.chat_data['task_id'])[0]  # TODO: fix case with no battles

    replay_url = "https://cups.online" + task_battle['visualizer_url'] + "?"
    for _ in range(10):
        replay_url += f"&player-names=" + urllib.parse.quote(names.get_name())
    #     replay_url += f"&client-ids=" + urllib.parse.quote(str(br['solution']['external_id']))
    replay_url += f"&replay=%2Fapi_v2%2Fbattles%2F{context.args[0]}%2Fget_result_file%2F"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text='Watch Replay', url=replay_url)]
    ])
    await update.message.reply_markdown("🔥", reply_markup=reply_markup)


game = PrefixHandler(cmd.PREFIXES, cmd.GAME, _game)


async def _plot_logins(cups_logins, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = allcups.task(context.chat_data['task_id'])

    # context.bot_data.pop('history', None)
    history = context.bot_data.get('history', {})
    context.bot_data['history'] = history
    task_history = history.get(context.chat_data['task_id'], [])
    history[context.chat_data['task_id']] = task_history

    ts = datetime.fromisoformat(task['start_date'])
    time_step = timedelta(minutes=15)
    now = datetime.now(timezone.utc) + time_step
    if task_history:
        ts = datetime.fromtimestamp(task_history[-1]['ts'], timezone.utc) + time_step

    while ts < now:
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
    for login in cups_logins:
        plot_data = []
        dates = []
        for h in task_history:
            point = None
            for s in h['leaderboard']:
                if s['login'].lower() == login.lower():
                    point = s['score']
                    break
            plot_data.append(point)
            dates.append(datetime.fromtimestamp(h['ts'], timezone.utc))

        plt.step(dates, plot_data, where='mid', label=login)
        # plt.plot(dates, plot_data, label=login)

    plt.grid(color='0.95')
    plt.legend(fontsize=16)

    plot_file = BytesIO()
    fig.tight_layout()
    fig.savefig(plot_file, format='png')
    plt.clf()
    plot_file.seek(0)

    await update.message.reply_photo(plot_file, caption="🔥")


async def _plot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не в🔥брана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    cups_logins = set(l for l in context.args)
    if not cups_logins:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    await _plot_logins(cups_logins, update, context)


plot = PrefixHandler(cmd.PREFIXES, cmd.PLOT, _plot)


async def _plot_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'contest_slug' not in context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее с🔥ревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
        return

    if 'task_id' not in context.chat_data:
        await update.message.reply_markdown("Для чата не в🔥брана задача. "
                                            f"Команда `!{cmd.TASK[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            logger.warning(f"Couldn't parse N for plot_top callback: {context.args[0]}")
            await update.message.reply_text("Ты меня ог🔥рчаешь")
            return
        if n == 0:
            await update.message.reply_text("C🔥mmandos")
            return
        if n < 0:
            await update.message.reply_text("Не н🔥до так")
            return

    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])[:n]
    logins = [s['user']['login'] for s in scores]

    await _plot_logins(logins, update, context)

plot_top = PrefixHandler(cmd.PREFIXES, cmd.PLOT_TOP, _plot_top)


def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))
    if update:
        update.message.reply_text(
            "Ур🔥!  Пр🔥изошла  неизветн🔥я  🔥шибка.  Мы  уже  зал🔥грировали  ее,  но  испр🔥влять  не  будем.")
