import logging

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(__name__)

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import redis

from chats_settings import ChatSettingsStorage
from settings import Config
from ai import handlers as ai_handlers
from ai import jobs as ai_jobs
from ai.forum import Forum as AIForum
from ai.chart import Chart as AIChart
from ml import handlers as ml_handlers
from subscriber import Subscriber
import handlers


def error_handler(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))


def run():
    config = Config()
    if not config.tg_token:
        logger.error("Telegram token is not specified")
        return

    logger.info(f"Starting bot with config: {str(config)}")

    updater = Updater(config.tg_token, use_context=True)

    # Specify custom "singleton" objects
    bot = updater.bot
    if config.redis_url:
        redis_storage = redis.from_url(config.redis_url)
    else:
        redis_storage = None
    bot.config = config
    bot.chat_settings = ChatSettingsStorage(redis_storage)
    bot.subscriber = Subscriber(redis_storage)

    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    dp.add_handler(handlers.start)
    dp.add_handler(handlers.subs_list)
    dp.add_handler(handlers.top)
    dp.add_handler(handlers.pos)
    dp.add_handler(handlers.configure)
    dp.add_handler(ai_handlers.subscribe_forum)
    dp.add_handler(ai_handlers.unsubscribe_forum)
    dp.add_handler(ai_handlers.top_n)
    dp.add_handler(ai_handlers.pos)
    dp.add_handler(ml_handlers.top_n)
    dp.add_handler(ml_handlers.pos)

    bot.ai_chart = AIChart(config.ai_chart_url, config.ai_chart_refresh_delay)
    bot.ai_forum = AIForum(config.forum_rss_url, redis_storage)
    job_queue = updater.job_queue
    job_queue.run_repeating(ai_jobs.gather_forum_updates,
                            config.forum_refresh_delay,
                            first=0.0,
                            context=bot.ai_forum)

    job_queue.run_repeating(ai_jobs.notify_about_forum_updates,
                            config.forum_notify_delay,
                            first=0.0,
                            context=bot.ai_forum)

    if config.host:
        logger.info("Host specified - starting webhook...")
        updater.start_webhook(listen="0.0.0.0", port=config.port, url_path=config.tg_token)
        updater.bot.set_webhook(config.host + config.tg_token)
    else:
        logger.info("Host is not specified - starting pooling...")
        updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    run()
