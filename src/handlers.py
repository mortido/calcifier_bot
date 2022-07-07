from functools import wraps, partial
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import PrefixHandler, ContextTypes, CallbackQueryHandler

import commands as cmd
import msg_formatter
import allcups

logger = logging.getLogger(__name__)


def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admins = update.effective_chat.get_administrators()
    admins_ids = [admin.user['id'] for admin in admins]
    return update.effective_user.id in admins_ids


def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return update.effective_user.username in context.bot_data['bot_admins']


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
    await update.message.reply_markdown(info_txt)


get_info = PrefixHandler(cmd.PREFIXES, cmd.INFO, _info)


async def _chat_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_login = context.chat_data.get('cups_login', set())
    cups_login |= usernames
    context.chat_data['cups_login'] = cups_login

    msg_txt = msg_formatter.chat_logins(cups_login)
    await update.message.reply_markdown(msg_txt)


chat_add = PrefixHandler(cmd.PREFIXES, cmd.CHAT_ADD, _chat_add)


async def _chat_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usernames = set(context.args)
    if not usernames:
        await update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    cups_login = context.chat_data.get('cups_login', set())
    cups_login.difference_update(usernames)
    context.chat_data['cups_login'] = cups_login

    msg_txt = msg_formatter.chat_logins(cups_login)
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

    cups_login = context.chat_data.get('cups_login', set())
    if not cups_login:
        await update.message.reply_markdown("Для чата не добавлены CUPS л🔥гины. "
                                            f"Команда `!{cmd.CHAT_ADD[0]}`")
        return

    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    task = allcups.task(context.chat_data['task_id'])
    scores = allcups.task_leaderboard(context.chat_data['task_id'])
    scores = [s for s in scores if s['user']['login'] in cups_login]

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




#
# @chat_admins_only
# def _subs_list(update: Update, context: CallbackContext):
#     chat_id = update.message.chat_id
#     subs = context.bot.subscriber.get_subs_by_chat(chat_id)
#     if not subs:
#         update.message.reply_text("Нет активных подписок")
#     else:
#         reply_rows = ["Ваши подписки:"]
#         reply_rows.append("```")
#         for s in subs:
#             reply_rows.append(str(s))
#
#         reply_rows.append("```")
#         update.message.reply_text("\n".join(reply_rows), parse_mode=ParseMode.MARKDOWN)
#
#
# subs_list = PrefixHandler(cmd.PREFIXES, cmd.SUBS, _subs_list)
#
#
#
#
#
#
# def _pos(update: Update, context: CallbackContext, short=True):
#     chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
#     if chat_settings.current_cup == CupType.AI:
#         return ai_handlers.pos_callback(update, context, short)
#     if chat_settings.current_cup == CupType.ML:
#         return ml_handlers.pos_callback(update, context, short)
#     update.message.reply_text("🔥❓")
#
#
# pos = PrefixHandler(cmd.PREFIXES, cmd.POS, partial(_pos, short=True))
# poos = PrefixHandler(cmd.PREFIXES, cmd.POOS, partial(_pos, short=False))
#
#
# async def _top(update: Update, context: CallbackContext, short=True):
#     chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
#     if chat_settings.current_cup == CupType.AI:
#         return ai_handlers.top_callback(update, context, short)
#     if chat_settings.current_cup == CupType.ML:
#         return ml_handlers.top_callback(update, context, short)
#     await update.message.reply_text("🔥❓")
#
#
# top = PrefixHandler(cmd.PREFIXES, cmd.TOP, partial(_top, short=True))
# toop = PrefixHandler(cmd.PREFIXES, cmd.TOOP, partial(_top, short=False))
#
#
# @chat_admins_only
# def _config(update: Update, context: CallbackContext):
#     update.message.reply_text("🔥")
#
#
# configure = PrefixHandler(cmd.CONFIG, cmd.TOP, _top)


def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))
    update.message.reply_text(
        "Ур🔥!  Пр🔥изошла  неизветн🔥я  🔥шибка.  Мы  уже  зал🔥грировали  ее,  но  испр🔥влять  не  будем.")
