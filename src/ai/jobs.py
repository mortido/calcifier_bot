from telegram.error import TelegramError
from telegram.ext import CallbackContext
from telegram import ParseMode

from subscriber import SubscriptionType
from ai import formatter
import logging

logger = logging.getLogger(__name__)


def gather_forum_updates(context: CallbackContext):
    forum = context.job.context
    forum.gather_updates()


def notify_about_forum_updates(context: CallbackContext):
    forum = context.job.context
    topics = forum.get_fresh_topics()
    subs = context.bot.subscriber.get_subs_by_type(SubscriptionType.AI_FORUM)
    logger.info(f"{subs} {topics}")
    if topics and subs:
        message = formatter.format_forum_updates(topics)
        for sub in subs:
            try:
                context.bot.send_message(chat_id=sub.chat_id, text=message,
                                         parse_mode=ParseMode.MARKDOWN)
            except TelegramError as e:
                logger.error(f"Error during sending ai forum update: {e}")
        forum.reset_to_timestamp(topics[0].last_update_timestamp)
