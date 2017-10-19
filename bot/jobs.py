# TODO: Threads to prevent waiting on request?... if so locks to notifier/chart is required

from telegram.error import TelegramError

import formatter


def gather_forum_updates(bot, job):
    job.context['forum'].check_updates()


def notify_about_forum_updates(bot, job):
    subs = job.context['notifier'].get_subscriptions_by_type('forum_updates')
    new_posts = job.context['forum'].get_updates()
    if new_posts:
        message = formatter.format_forum_updates(new_posts)
        for sub in subs:
            try:
                bot.send_message(chat_id=sub['chat_id'], text=message, parse_mode='Markdown')
            except TelegramError as e:
                print(e)
                pass

    job.context['forum'].reset_changes()
