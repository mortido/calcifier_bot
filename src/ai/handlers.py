from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext, PrefixHandler

import src.commands as commands
from src.common import chat_admins_only
from src.subscriber import SubscriptionType
from ai import formatter
import logging

logger = logging.getLogger(__name__)


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


def top_n_callback(update: Update, context: CallbackContext):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=ChatAction.TYPING)

    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            logger.warning(f"Couldn't parse N for ai top callback: {context.args[0]}")
            update.message.reply_text("🔥❓")
            return
        if n < 1:
            update.message.reply_text("🐴❤️")
            return
    players = context.bot.ai_chart.get_top_n(n)
    text = formatter.format_top(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


top_n = PrefixHandler(commands.PREFIXES, commands.TOP_AI, top_n_callback)


def pos_callback(update: Update, context: CallbackContext):
    usernames = context.args
    if not usernames:
        update.message.reply_text("Ст🔥ит ук🔥з🔥ть ник")
        return
    players = context.bot.ai_chart.get_pos(usernames)
    if not players:
        update.message.reply_text("Не н🔥шел т🔥ких уч🔥стник🔥в")
        return

    text = formatter.format_pos(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)



pos = PrefixHandler(commands.PREFIXES, commands.POS_AI, pos_callback)
