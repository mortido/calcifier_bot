from telegram import Update, ChatAction
from telegram.ext import CallbackContext, PrefixHandler
from functools import partial

import src.commands as commands
from common import chat_admins_only
from src.subscriber import SubscriptionType
import logging

logger = logging.getLogger(__name__)


def top_callback(update: Update, context: CallbackContext, short=True):
    update.message.reply_text("🔥")


top = PrefixHandler(commands.PREFIXES, commands.TOP_ML, partial(top_callback, short=True))
toop = PrefixHandler(commands.PREFIXES, commands.TOOP_ML, partial(top_callback, short=False))


def pos_callback(update: Update, context: CallbackContext, short=True):
    update.message.reply_text("🔥")


pos = PrefixHandler(commands.PREFIXES, commands.POS_ML, partial(pos_callback, short=True))
poos = PrefixHandler(commands.PREFIXES, commands.POOS_ML, partial(pos_callback, short=False))
