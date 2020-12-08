from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext, PrefixHandler
from functools import partial

import src.commands as commands
from src.common import chat_admins_only
from src.subscriber import SubscriptionType
from ai import formatter
import logging

logger = logging.getLogger(__name__)

MAX_USERNAMES = 30


@chat_admins_only
def _subscribe_games(update: Update, context: CallbackContext):
    usernames = context.args
    if not usernames:
        update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    chat_id = update.message.chat_id
    sub = context.bot.subscriber.get_sub(chat_id, SubscriptionType.AI_GAMES)
    if sub is None:
        usernames = set(usernames[:MAX_USERNAMES])
        context.bot.subscriber.add_sub(chat_id, SubscriptionType.AI_GAMES, usernames)
        update.message.reply_text(f"Подписка на системные игры создана")
    else:
        if len(usernames) + len(sub.data) > MAX_USERNAMES:
            usernames = usernames[:MAX_USERNAMES - len(sub.data)]

        sub.data |= set(usernames)
        context.bot.subscriber.update_sub(sub)
        update.message.reply_text(
            f"Подписка на игры обновлена, текущие ники: *{', '.join(sub.data)}*",
            parse_mode=ParseMode.MARKDOWN)


subscribe_games = PrefixHandler(commands.PREFIXES, commands.SUB_AI_GAMES, _subscribe_games)


@chat_admins_only
def _unsubscribe_games(update: Update, context: CallbackContext):
    usernames = context.args
    if not usernames:
        update.message.reply_text("Ст🔥ит  ук🔥зать  ник")
        return

    chat_id = update.message.chat_id
    sub = context.bot.subscriber.get_sub(chat_id, SubscriptionType.AI_GAMES)
    if sub is None:
        update.message.reply_text("Нет активных п🔥дписок на системные игры")
        return

    sub.data.difference_update(set(usernames))
    if sub.data:
        context.bot.subscriber.update_sub(sub)
        update.message.reply_text(
            f"Подписка на игры обновлена, текущие ники: *{', '.join(sub.data)}*",
            parse_mode=ParseMode.MARKDOWN)
    else:
        context.bot.subscriber.remove_sub(chat_id, SubscriptionType.AI_GAMES)
        update.message.reply_text(f"Вы отписались от всех системных игр")


unsubscribe_games = PrefixHandler(commands.PREFIXES, commands.UNSUB_AI_GAMES, _unsubscribe_games)


def _subscribe_ai_chat_top(update: Update, context: CallbackContext):
    usernames = set(context.args)
    if not usernames:
        update.message.reply_text("Ст🔥ит  указ🔥ть  ник")
        return

    chat_id = update.message.chat_id
    sub = context.bot.subscriber.get_sub(chat_id, SubscriptionType.AI_CHAT_TOP)
    if sub is None:
        context.bot.subscriber.add_sub(chat_id, SubscriptionType.AI_CHAT_TOP, usernames)
    else:
        sub.data |= usernames
        context.bot.subscriber.update_sub(sub)
        usernames = sub.data
    update.message.reply_text(
        f"Топ чата: *{', '.join(sorted(usernames))}*",
        parse_mode=ParseMode.MARKDOWN)


subscribe_ai_chat_top = PrefixHandler(commands.PREFIXES, commands.SUB_AI_CHAT_TOP,
                                      _subscribe_ai_chat_top)


def _unsubscribe_ai_chat_top(update: Update, context: CallbackContext):
    usernames = set(context.args)
    if not usernames:
        update.message.reply_text("Ст🔥ит  ук🔥зать  ник")
        return

    chat_id = update.message.chat_id
    sub = context.bot.subscriber.get_sub(chat_id, SubscriptionType.AI_CHAT_TOP)
    if sub is None:
        update.message.reply_text("Топ чата пуст")
        return

    sub.data.difference_update(usernames)
    if sub.data:
        context.bot.subscriber.update_sub(sub)
        update.message.reply_text(
            f"Топ чата: *{', '.join(sorted(sub.data))}*",
            parse_mode=ParseMode.MARKDOWN)
    else:
        context.bot.subscriber.remove_sub(chat_id, SubscriptionType.AI_CHAT_TOP)
        update.message.reply_text(f"Топ чата пуст")


unsubscribe_ai_chat_top = PrefixHandler(commands.PREFIXES, commands.UNSUB_AI_CHAT_TOP,
                                        _unsubscribe_ai_chat_top)


def top_callback(update: Update, context: CallbackContext, short=True):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=ChatAction.TYPING)

    n = 10
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            logger.warning(f"Couldn't parse N for ai top callback: {context.args[0]}")
            update.message.reply_text("Ты  меня  ог🔥рчаешь")
            return
        if n == 0:
            update.message.reply_text("C🔥mmandos")
            return
        if n < 0:
            update.message.reply_text("Не  н🔥до так")
            return
    players = context.bot.ai_chart.get_top(n)
    if short:
        text = formatter.format_top(context.bot.ai_chart.name, players)
    else:
        text = formatter.format_toop(context.bot.ai_chart.name, players)
    if len(text) > 4000:
        text = text[:-3][:4000] + ".🔥..🔥🔥```"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


top = PrefixHandler(commands.PREFIXES, commands.TOP_AI, partial(top_callback, short=True))
toop = PrefixHandler(commands.PREFIXES, commands.TOOP_AI, partial(top_callback, short=False))


def pos_callback(update: Update, context: CallbackContext, short=True):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=ChatAction.TYPING)

    usernames = context.args
    if not usernames:
        update.message.reply_text("Ст🔥ит  ук🔥зать  ник")
        return
    players = context.bot.ai_chart.get_pos(usernames)
    if not players:
        update.message.reply_text("Не  н🔥шел  таких  участник🔥в")
        return

    if short:
        text = formatter.format_pos(context.bot.ai_chart.name, players)
    else:
        text = formatter.format_poos(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


pos = PrefixHandler(commands.PREFIXES, commands.POS_AI, partial(pos_callback, short=True))
poos = PrefixHandler(commands.PREFIXES, commands.POOS_AI, partial(pos_callback, short=False))


def chat_top_callback(update: Update, context: CallbackContext, short=True):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=ChatAction.TYPING)

    chat_id = update.message.chat_id
    sub = context.bot.subscriber.get_sub(chat_id, SubscriptionType.AI_CHAT_TOP)
    if not sub or not sub.data:
        update.message.reply_text("Т🔥п  чат🔥 пуст")
        return
    players = context.bot.ai_chart.get_pos(sub.data)
    if short:
        text = formatter.format_pos(context.bot.ai_chart.name, players)
    else:
        text = formatter.format_poos(context.bot.ai_chart.name, players)
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

chat_top = PrefixHandler(commands.PREFIXES, commands.CHAT_TOP, partial(chat_top_callback, short=True))
chat_toop = PrefixHandler(commands.PREFIXES, commands.CHAT_TOOP, partial(chat_top_callback, short=False))