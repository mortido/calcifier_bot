from telegram import Update, ParseMode
from telegram.ext import CallbackContext, PrefixHandler
from functools import wraps
import commands
from settings import config


def chat_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext):

        if update.message.chat.type != 'private':
            admins_ids = [admin.user['id'] for admin in update.message.chat.get_administrators()]
            if update.message.from_user.id not in admins_ids:
                return None
        return func(update, context)

    return wrapper


def bot_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        if update.message.from_user.username not in config.admins:
            return None
        return func(update, context)

    return wrapper


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
    reply_rows.append(f"/{commands.POS_AI[0]} - not implemented yet")
    reply_rows.append(f"/{commands.TOP_AI[0]} - not implemented yet")

    reply_rows.append("")
    reply_rows.append(
        f"Для отключения подписок используйте unsub команды, например /{commands.UNSUB_AI_FORUM[0]}")

    update.message.reply_text("\n".join(reply_rows))


start = PrefixHandler(commands.PREFIXES, commands.HELP, _start)
