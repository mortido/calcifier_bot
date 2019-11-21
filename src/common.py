from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from functools import wraps


def chat_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext):

        if update.message.chat.type != 'private':
            admins_ids = [admin.user['id'] for admin in update.message.chat.get_administrators()]
            if update.message.from_user.id not in admins_ids:
                return None
        return func(update, context)

    return wrapper

@chat_admins_only
def _subs_list(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    subs = context.bot.subscriber.get_subs_by_chat(chat_id)
    reply_rows = ["1"]
    for s in subs:
        reply_rows.append(f"{s.type}")
    update.message.reply_text("\n".join(reply_rows))


subs_list = CommandHandler("subs", _subs_list)