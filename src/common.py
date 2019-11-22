from telegram import Update
from telegram.ext import CallbackContext
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


def bot_admins_only(func):
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext):
        if update.message.from_user.username not in context.bot.config.admins:
            return None
        return func(update, context)

    return wrapper
