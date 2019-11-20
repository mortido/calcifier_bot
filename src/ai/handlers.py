from telegram import Update
from telegram.ext import CallbackContext, Filters, CommandHandler

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
            'Не удалось подписаться.\nВозможно подписка уже существует, для проверки: /subs')


subscribe_forum = CommandHandler("sub_aiforum", _subscribe_forum)
# @chat_admins_only
# def unsubscribe_forum(update: Update, context: CallbackContext):
#     chat_id = update.message.chat_id
#     subs = notifier.get_subscriptions_by_chat_and_type(chat_id, 'forum_updates')
#     if subs:
#         for sub in subs:
#             notifier.remove_subscription_by_id(sub['id'])
#         update.message.reply_text('Подписка отключена')
#     else:
#         update.message.reply_text('Нет активных подписок')
