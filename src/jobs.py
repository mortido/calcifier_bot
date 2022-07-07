import logging
import time
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

import allcups
import msg_formatter

logger = logging.getLogger(__name__)


async def _process_battle_results(battle, context: ContextTypes.DEFAULT_TYPE) -> None:
    battle_subs = context.bot_data.get('battle_subs', dict())
    logins = [r['user']['login'] for r in battle['battle_results']]
    for login in logins:
        if login in battle_subs:
            scores = []
            for i, r in enumerate(battle['battle_results']):
                scores.append({
                    'rank': i + 1,
                    'login': r['user']['login'],
                    'mark': login == r['user']['login'],
                    'score': r['user']['score'],
                    'id': r['user']['solution']['id'],
                    'language': r['user']['solution']['language']['name'],
                })
                mag_txt = msg_formatter.format_game(scores)
                for chat_id in battle_subs[login]:
                    await context.bot.send_message(chat_id=chat_id,
                                                   text=msg_txt,
                                                   parse_mode='markdown')
                    time.sleep(1 / 10)


async def games_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    battles = allcups.battles()
    now = datetime.now(timezone.utc)
    battle_last_id = context.bot_data.get('battle_last_id', dict())
    context.bot_data['battle_last_id'] = battle_last_id
    for b in battles:
        end_date = datetime.fromisoformat(b['finish_date'])
        if now > end_date:
            continue
        for r in b['rounds']:
            start_date = datetime.fromisoformat(r['start_date'])
            end_date = datetime.fromisoformat(r['finish_date'])
            if now < start_date or now > end_date:
                continue
            for t in r['tasks']:
                name = f"{b['name']}: {r['name']}: {t['name']}"
                last_id = battle_last_id.get(t['id'], None)
                task_battles = allcups.battles(t['id'], last_id)
                if task_battles:  # and last_id:
                    battle_last_id[t['id']] = task_battles[0]['id']
                    for battle in task_battles:
                        await _process_battle_results(battle, context)

# def notify_about_new_games(context: CallbackContext):
#     chart = context.job.context
#     new_games = chart.get_new_games()
#     if new_games:
#         new_games.reverse()
#         subs = context.bot.subscriber.get_subs_by_type(SubscriptionType.AI_GAMES)
#         try:
#             for sub in subs:
#                 for game in new_games:
#                     post_it = False
#                     player_idx = -1
#                     for i, player in enumerate(game.players):
#                         if player in sub.data:
#                             post_it = True
#                             player_idx = i
#                             game.players[i] = player
#                     if post_it:
#                         context.bot.send_message(chat_id=sub.chat_id,
#                                                  text=formatter.format_game(game, player_idx),
#                                                  disable_web_page_preview=True,
#                                                  parse_mode=ParseMode.MARKDOWN)
#                         time.sleep(1/10)
#         except BaseException as e:
#             logger.error(f"Error during sending ai games: {e}")
#         chart.reset_to_game(new_games[-1].gid)
