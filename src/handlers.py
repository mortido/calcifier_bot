from telegram import Update, ParseMode
from telegram.ext import CallbackContext, PrefixHandler
from functools import wraps

import commands
from ai import handlers as ai_handlers
from ml import handlers as ml_handlers
from chats_settings import CupType
from common import chat_admins_only


@chat_admins_only
def _subs_list(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    subs = context.bot.subscriber.get_subs_by_chat(chat_id)
    if not subs:
        update.message.reply_text("Нет активных подписок")
    else:
        reply_rows = ["Ваши подписки:"]
        reply_rows.append("```")
        for s in subs:
            text = f"{s.type.value}"
            if s.data is not None:
                text += f": {str(s.data)}"
            reply_rows.append(text)

        reply_rows.append("```")
        update.message.reply_text("\n".join(reply_rows), parse_mode=ParseMode.MARKDOWN)


subs_list = PrefixHandler(commands.PREFIXES, commands.SUBS, _subs_list)


# TODO: get/update bot config (e.g. urls)
# TODO: admin console: config manipulation,


@chat_admins_only
def _start(update: Update, context: CallbackContext):
    reply_rows = ["🔥💬"]
    reply_rows.append(f"/{commands.SUBS[0]} - Список активных подписок")
    reply_rows.append(f"/{commands.SUB_AI_FORUM[0]} - подписка на обновление RAIC форума")
    reply_rows.append(f"/{commands.CONFIG[0]} - настройка бота")

    reply_rows.append(f"/{commands.POS_AI[0]} [nickname...] - позиции участников в AI Cup")
    reply_rows.append(f"/{commands.TOP_AI[0]} [N] - топ участников AI Cup")
    reply_rows.append(f"/{commands.POS_ML[0]} [nickname...] - позиции участников в ML Cup")
    reply_rows.append(f"/{commands.TOP_ML[0]} [N] - топ участников ML Cup")
    reply_rows.append("")

    chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
    reply_rows.append(f"Текущий чемпионат: `{chat_settings.current_cup.value}`")
    reply_rows.append(f"/{commands.POS[0]} [nickname...] - позиции участников")
    reply_rows.append(f"/{commands.TOP[0]} [N] - топ участников")

    reply_rows.append(
        f"Для отключения подписок используйте unsub команды, например /{commands.UNSUB_AI_FORUM[0]}")

    update.message.reply_text("\n".join(reply_rows))


start = PrefixHandler(commands.PREFIXES, commands.HELP, _start)


def _pos(update: Update, context: CallbackContext):
    chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
    if chat_settings.current_cup == CupType.AI:
        return ai_handlers.pos_callback(update, context)
    if chat_settings.current_cup == CupType.ML:
        return ml_handlers.pos_callback(update, context)
    update.message.reply_text("🔥❓")


pos = PrefixHandler(commands.PREFIXES, commands.POS, _pos)


def _top(update: Update, context: CallbackContext):
    chat_settings = context.bot.chat_settings.get_settings(update.message.chat_id)
    if chat_settings.current_cup == CupType.AI:
        return ai_handlers.top_n_callback(update, context)
    if chat_settings.current_cup == CupType.ML:
        return ml_handlers.top_n_callback(update, context)
    update.message.reply_text("🔥❓")


top = PrefixHandler(commands.PREFIXES, commands.TOP, _top)


@chat_admins_only
def _config(update: Update, context: CallbackContext):
    update.message.reply_text("🔥")


configure = PrefixHandler(commands.CONFIG, commands.TOP, _top)
