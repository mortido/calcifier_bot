import logging
import argparse
import json
import os

from telegram import ForceReply, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler, filters,
                          PicklePersistence)

import allcups
import configuration
import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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
    persistent_storage = PicklePersistence(filepath=config.persistent_file)


    application = Application.builder().token(config.tg_token)\
        .persistence(persistence=persistent_storage).build()

    application.add_error_handler(handlers.error_handler)
    application.add_handler(handlers.start)
    application.add_handler(handlers.set_contest)
    application.add_handler(handlers.top)

    application.run_polling()


if __name__ == '__main__':
    main()
