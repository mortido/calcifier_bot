import logging

from telegram.ext import Updater, CommandHandler

import jobs
import storage
from forum import Forum
from notifier import Notifier
import os

# TODO: log errors to telegram
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)

notifier = None
chart = None


def error_handler(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def subscribe_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0 and update.message.from_user['id'] not in [admin.user['id'] for admin in update.message.chat.get_administrators()]:
        return

    subs = notifier.get_subscriptions_by_chat_and_type(chat_id, 'forum_updates')
    if not subs:
        update.message.reply_text('Подписался')
        notifier.add_subscription(chat_id, 'forum_updates')


def unsubscribe_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0 and update.message.from_user['id'] not in [admin.user['id'] for admin in update.message.chat.get_administrators()]:
        return

    subs = notifier.get_subscriptions_by_chat_and_type(chat_id, 'forum_updates')
    if subs:
        for sub in subs:
            notifier.remove_subscription_by_id(sub['id'])
        update.message.reply_text('Подписка отключена')
    else:
        update.message.reply_text('Нет активных подписок')


def main():
    global notifier, chart

    config = storage.load_from_file('config.json')
    if config is None:
        print("Can't open configuration file")
        return

    chart = Forum(config['forum_rss_url'], config['forum_date_file_name'])
    notifier = Notifier(config['subscriptions_file_name'])

    # updater = Updater(config['auth_token'])
    TOKEN = os.getenv("TG_TOKEN", "")
    if not TOKEN:
        logger.error("No telegram token is specified")
        return
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    dp.add_handler(CommandHandler("subscribe", subscribe_handler))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))

    job_queue = updater.job_queue
    job_queue.run_repeating(jobs.gather_forum_updates,
                            config['update_rate'],
                            first=0.0,
                            context={
                                'forum': chart
                            })

    job_queue.run_repeating(jobs.notify_about_forum_updates,
                            config['notify_rate'],
                            first=0.0,
                            context={
                                'notifier': notifier,
                                'forum': chart,
                            })

    updater.start_polling()
    updater.idle()

    PORT = int(os.environ.get('PORT', '8443'))
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook("https://<appname>.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == "__main__":
    main()
