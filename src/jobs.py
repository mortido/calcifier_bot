import logging
import time
from datetime import datetime, timezone
import urllib.parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden

import allcups
import msg_formatter
import names

logger = logging.getLogger(__name__)


async def _process_battle_results(battle, name, lb_scores,
                                  context: ContextTypes.DEFAULT_TYPE) -> None:
    battle_subs = context.bot_data.get('battle_subs', dict())
    logins = [r['user__login'] for r in battle['user_results']]
    for login in logins:
        if login not in battle_subs:
            continue

        scores = []
        sorted_results = list(
            sorted(battle['user_results'], key=lambda x: x['score'], reverse=True))
        win = False
        solution = -1
        for i, r in enumerate(sorted_results):
            if login == r['user__login']:
                win = (i + 1) <= (len(sorted_results) // 2)
                solution = r['solution_id']

            score = {
                'rank': i + 1,
                'login': r['user__login'],
                'sub_flag': login == r['user__login'],
                'score': r['score'],
                'id': r['solution_id'],
                'language': r['language__name'],
            }
            if r['user__login'] in lb_scores:
                score['lb_score'] = lb_scores[r['user__login']]['score']
                score['lb_rank'] = lb_scores[r['user__login']]['rank']
            else:
                score['lb_score'] = "-"
                score['lb_rank'] = "-"
            scores.append(score)

        msg_txt = msg_formatter.format_game(battle, name, scores, lb_scores[login], win, solution)

        replay_url = "https://cups.online" + battle['visualizer_url'] + "?"
        for br in battle['user_results']:
            replay_url += f"&player-names=" + urllib.parse.quote(br['user__login'])
            # replay_url += f"&player-names=" + urllib.parse.quote(names.get_name())
            replay_url += f"&client-ids=" + urllib.parse.quote(str(br['solution__external_id']))
        replay_url += f"&replay=" + urllib.parse.quote(battle['battle_result_file'])
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Watch Replay', url=replay_url)]
        ])

        blocked = []
        for chat_id in battle_subs[login]:
            try:
                await context.bot.send_message(chat_id=chat_id,
                                               text=msg_txt,
                                               parse_mode='markdown',
                                               reply_markup=reply_markup)
            except Forbidden as e:
                logger.warning(f"Bot blocked by '{chat_id}' - removing subscription.")
                blocked.append(chat_id)
                context.application.chat_data[chat_id].pop('battle_login', None)
            except Exception as e:
                logger.warning(f"Error sending game subscription: {e}")
            time.sleep(1 / 10)
        if blocked:
            battle_subs[login] = [s for s in battle_subs[login] if s not in blocked]
    context.bot_data['battle_subs'] = battle_subs


async def games_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    battles = allcups.battles()
    now = datetime.now(timezone.utc)

    sent_battle_ids = context.bot_data.get('sent_battle_ids', dict())
    context.bot_data['sent_battle_ids'] = sent_battle_ids

    # battle_updates = context.bot_data.get('battle_updates', dict())
    # context.bot_data['battle_updates'] = battle_updates

    # battle_last_id = context.bot_data.get('battle_last_id', dict())
    # context.bot_data['battle_last_id'] = battle_last_id
    context.bot_data.pop('battle_last_id', None)
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
                sent_ids = sent_battle_ids.get(t['id'], set())
                # battle_update = battle_updates.get(t['id'], None)
                task_battles = allcups.battles_bot(t['id'])

                if not task_battles:
                    continue

                scores = allcups.task_leaderboard(t['id'])
                lb_scores = {}
                for s in scores:
                    lb_scores[s['user']['login']] = {
                        'rank': s['rank'],
                        'score': s['score'],
                    }

                for battle in task_battles[::-1]:
                    if battle['id'] in sent_ids:
                        continue
                    if battle['status'] != 'DONE':
                        continue
                    await _process_battle_results(battle, name, lb_scores, context)
                    sent_ids.add(battle['id'])

                sent_battle_ids[t['id']] = set(sorted(sent_ids, reverse=True)[:5000])

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
