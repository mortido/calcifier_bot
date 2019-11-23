from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext, PrefixHandler
from functools import partial

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

@chat_admins_only
def _subscribe_games(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    # if context.bot.subscriber.add_sub(chat_id, SubscriptionType.AI_FORUM):
    #     update.message.reply_text('Добавлена подписка на обновление RAIC форума')
    # else:
    #     update.message.reply_text(
    #         'Не удалось подписаться.\nВозможно, подписка уже существует, для проверки: /subs')


subscribe_games = PrefixHandler(commands.PREFIXES, commands.SUB_AI_GAMES, _subscribe_games)

@chat_admins_only
def _unsubscribe_games(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    # if context.bot.subscriber.remove_sub(chat_id, SubscriptionType.AI_FORUM):
    #     update.message.reply_text('Подписка на обновление RAIC форума отключена')
    # else:
    #     update.message.reply_text(
    #         'Не удалось отписаться.\nВозможно, подписки и нет, для проверки: /subs')


unsubscribe_games = PrefixHandler(commands.PREFIXES, commands.UNSUB_AI_GAMES, _unsubscribe_games)

def top_callback(update: Update, context: CallbackContext, short=True):
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
    players = context.bot.ai_chart.get_top(n)
    if short:
        text = formatter.format_top(context.bot.ai_chart.name, players)
    else:
        text = formatter.format_toop(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


top = PrefixHandler(commands.PREFIXES, commands.TOP_AI, partial(top_callback, short=True))
toop = PrefixHandler(commands.PREFIXES, commands.TOOP_AI, partial(top_callback, short=False))


def pos_callback(update: Update, context: CallbackContext, short=True):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=ChatAction.TYPING)

    usernames = context.args
    if not usernames:
        update.message.reply_text("Ст🔥ит ук🔥з🔥ть ник")
        return
    players = context.bot.ai_chart.get_pos(usernames)
    if not players:
        update.message.reply_text("Не н🔥шел т🔥ких уч🔥стник🔥в")
        return

    if short:
        text = formatter.format_pos(context.bot.ai_chart.name, players)
    else:
        text = formatter.format_poos(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


pos = PrefixHandler(commands.PREFIXES, commands.POS_AI, partial(pos_callback, short=True))
poos = PrefixHandler(commands.PREFIXES, commands.POOS_AI, partial(pos_callback, short=False))
