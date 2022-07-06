from functools import wraps, partial
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import PrefixHandler, ContextTypes, filters

import commands as cmd
import formatter
import allcups

logger = logging.getLogger(__name__)


def chat_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.chat.type != 'private':
            admins_ids = [admin.user['id'] for admin in update.message.chat.get_administrators()]
            if update.message.from_user.id not in admins_ids:
                return None
        return func(update, context)
    return wrapper


# def bot_admins_only(func):
#     @wraps(func)
#     def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
#         if update.message.from_user.username not in context.bot.config.admins:
#             return None
#         return func(update, context)
#
#     return wrapper



@chat_admins_only
async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_rows = ["🔥💬"]
    # reply_rows.append(f"/{cmd.SUBS[0]} - Список активных подписок")
    # reply_rows.append(f"/{cmd.SUB_AI_GAMES[0]} nickname... - подписка на системные игры")
    # reply_rows.append(f"/{cmd.CONFIG[0]} - настройка бота")
    # reply_rows.append("")
    # chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
    # reply_rows.append(f"Текущий чемпионат: `{chat_settings.current_cup.value}`")
    # reply_rows.append(f"/{cmd.POS[0]} [nickname...] - позиции участников")
    # reply_rows.append(f"/{cmd.TOP[0]} [N] - топ участников")
    #
    # reply_rows.append(
    #     f"Для отключения подписок используйте unsub команды, например /{cmd.UNSUB_AI_GAMES[0]}")

    await update.message.reply_text("\n".join(reply_rows))

start = PrefixHandler(cmd.PREFIXES, cmd.HELP, _start)


@chat_admins_only
async def _set_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    if len(context.args) != 1:
        await update.message.reply_text("🔥❓")
        return
    slug = context.args[0]

    contests = allcups.contests()
    contest = None
    for c in contests:
        if c['slug'] == slug:
            contest = c
            break

    if contest is None:
        logger.warning(f"There is no contest with slug `{slug}`")
        await update.message.reply_markdown(f"There is no c🔥ntest with slug `{slug}`")
        return

    context.chat_data['contest_slug'] = slug
    lines = [
        "Для чата установлено новое соревнование:",
        "```",
        f"Трек: {', '.join(contest['categories'])}",
        f"Назваине: {contest['name']}",
        "```",
    ]
    await update.message.reply_markdown("\n".join(lines))


set_contest = PrefixHandler(cmd.PREFIXES, cmd.CONTEST, _set_contest)


async def _top(update: Update, context: ContextTypes.DEFAULT_TYPE, short: bool) -> None:
    if 'contest_slug' not in  context.chat_data:
        await update.message.reply_markdown("Для чата не установлено текущее соревнование. "
                                            f"Команда `!{cmd.CONTEST[0]} %CONTEST_SLUG%`")
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

    contest = allcups.contest_navigation(context.chat_data['contest_slug'])['contest']
    last_task = None
    for stage in contest['stages']:
        for r in stage['rounds']:
            for task in r['tasks']:
                last_task = task

    if last_task is None:
        logger.warning(f"Couldn't find last task for {context.chat_data['contest_slug']}")
        await update.message.reply_text("Для текущего с🔥ревнования не нашлось задач.")
        return

    scores = allcups.task_leaderboard(last_task['id'])[:n]
    if short:
        text = formatter.format_top(last_task['name'], scores)
    else:
        text = formatter.format_toop(last_task['name'], scores)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    await update.message.reply_markdown(text)


top = PrefixHandler(cmd.PREFIXES, cmd.TOP, partial(_top, short=True))
toop = PrefixHandler(cmd.PREFIXES, cmd.TOOP, partial(_top, short=False))









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
    update.message.reply_text("Ур🔥!  Пр🔥изошла  неизветн🔥я  🔥шибка.  Мы  уже  зал🔥грировали  ее,  но  испр🔥влять  не  будем.")
