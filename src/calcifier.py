import logging
import argparse
import json
import os
import asyncio
from datetime import datetime, timezone

from telegram import ForceReply, Update
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler, filters,
                          PicklePersistence, PersistenceInput)

import allcups
import configuration
import handlers
import jobs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
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

    logger.info(f"Starting Calcifier bot... ")
    logger.info(f"Persistent file: {config.persistent_file}")

    # Using JSON can broke some sets
    persistent_storage = PicklePersistence(filepath=config.persistent_file)

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(persistent_storage.update_bot_data({'bot_admins': config.bot_admins}))

    application = Application.builder().token(config.tg_token)\
        .persistence(persistence=persistent_storage).build()
    #
    # logger.info(f"Bot admins: {', '.join(config.bot_admins)}")
    # application.admins = config.bot_admins

    job_queue = application.job_queue
    async def set_bot_admins(c):
        logger.info(f"Setting bot_data...")
        logger.info(f"Bot admins: {', '.join(config.bot_admins)}")
        c.bot_data['bot_admins'] = config.bot_admins
    job_queue.run_once(set_bot_admins, 5)
    job_queue.run_repeating(jobs.games_notifications, interval=1*60, first=5)

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
    application.add_handler(handlers.pos)
    application.add_handler(handlers.sub)
    application.add_handler(handlers.unsub)
    application.add_handler(handlers.game)
    application.add_handler(handlers.games)
    application.add_handler(handlers.plot)
    application.add_handler(handlers.plotl)
    application.add_handler(handlers.plot_top)
    application.add_handler(handlers.plotl_top)
    application.add_handler(handlers.plot_chat)
    application.add_handler(handlers.plotl_chat)

    application.run_polling()


if __name__ == '__main__':
    main()
