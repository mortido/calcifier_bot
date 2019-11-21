from telegram import Update
from telegram.ext import CallbackContext, PrefixHandler

import src.commands as commands
from src.common import chat_admins_only
from src.subscriber import SubscriptionType
import logging

logger = logging.getLogger(__name__)

__all__ = ["subscribe_forum"]


@chat_admins_only
def _subscribe_forum(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if context.bot.subscriber.add_sub(chat_id, SubscriptionType.AI_FORUM):
        update.message.reply_text('Добавлена подписка на обновление RAIC форума')
    else:
        update.message.reply_text(
            'Не удалось подписаться.\nВозможно, подписка уже существует, для проверки: /subs')


subscribe_forum = PrefixHandler(commands.PREFIXES, commands.SUB_AI_FORUM, _subscribe_forum)


@chat_admins_only
def _unsubscribe_forum(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if context.bot.subscriber.remove_sub(chat_id, SubscriptionType.AI_FORUM):
        update.message.reply_text('Подписка на обновление RAIC форума отключена')
    else:
        update.message.reply_text(
            'Не удалось отписаться.\nВозможно, подписки и нет, для проверки: /subs')


unsubscribe_forum = PrefixHandler(commands.PREFIXES, commands.UNSUB_AI_FORUM, _unsubscribe_forum)
