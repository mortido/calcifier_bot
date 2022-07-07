import logging
import argparse
import json
import os

from telegram import ForceReply, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler, filters,
                          PicklePersistence, PersistenceInput)

import allcups
import configuration
import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():

    # print(allcups.task_leaderboard("1058"))

    parser = argparse.ArgumentParser(
        description='Calcifer telegram bot.'
    )
    parser.add_argument(
        '-c', '--config-file', type=str, required=False, default="etc/config.json",
        help='Path to config.json file'
    )
    args = parser.parse_args()

    config = configuration.from_json_file(args.config_file)
    os.makedirs(os.path.dirname(config.persistent_file), exist_ok=True)

    logger.info(f"Starting Calcifier bot... "
                f"Persistent file: {config.persistent_file}")

    # Using JSON can broke some sets
    persistent_storage = PicklePersistence(filepath=config.persistent_file,
                                           store_data=PersistenceInput(bot_data=False))


    application = Application.builder().token(config.tg_token)\
        .persistence(persistence=persistent_storage).build()
    application.bot_data['bot_admins'] = config.bot_admins
    logger.info(f"Bot admins: {', '.join(config.bot_admins)}")

    application.add_error_handler(handlers.error_handler)
    application.add_handler(handlers.start)
    application.add_handler(handlers.get_info)
    application.add_handler(handlers.set_contest)
    application.add_handler(handlers.set_task)
    application.add_handler(handlers.choose_task)
    application.add_handler(handlers.top)
    application.add_handler(handlers.chat_add)
    application.add_handler(handlers.chat_remove)
    application.add_handler(handlers.chat_top)

    application.run_polling()


if __name__ == '__main__':
    main()
