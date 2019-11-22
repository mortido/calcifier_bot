from telegram import Update, ChatAction
from telegram.ext import CallbackContext, PrefixHandler

import src.commands as commands
from common import chat_admins_only
from src.subscriber import SubscriptionType
import logging

logger = logging.getLogger(__name__)


def top_n_callback(update: Update, context: CallbackContext):
    update.message.reply_text("🔥")


top_n = PrefixHandler(commands.PREFIXES, commands.TOP_ML, top_n_callback)


def pos_callback(update: Update, context: CallbackContext):
    update.message.reply_text("🔥")


pos = PrefixHandler(commands.PREFIXES, commands.POS_ML, pos_callback)
