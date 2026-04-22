import os
import requests
from datetime import datetime
from . import db
from .models import UserStats, Leaderboard

WORDLE_API_URL = os.getenv('WORDLE_API_URL', 'https://navigably-phytosociologic-lorraine.ngrok-free.dev')

last_polled = None

def poll_wordlegame():
    global last_polled

    print(f'[poller] polling at {datetime.now()}')

    try:
        params = {}

        if last_polled:
            params['completed_after'] = last_polled.isoformat()

        response = requests.get(
            f'{WORDLE_API_URL}/games',
            params=params,
            timeout=5
        )

        if response.status_code != 200:
            print(f'[poller] API returned {response.status_code}, skipping')
            return
        
        games = response.json()

        if not games:
            print('[poller] no new games to process')
            last_polled = datetime.utcnow()
            return
        
        for game in games:
            process_game(game)

        last_polled = datetime.utcnow()
        print(f'[poller] processed {len(games)} games')

    except requests.exceptions.ConnectionError:
        print('[poller] could not reach wordle API, will retry next interval')
    except Exception as e:
        print(f'[poller] unexpected error: {e}')

def process_game(game):
    user_id = game['user_id']
    username = game['username']
    won = game['won']
    guesses = game['guess_count']

    update_user_stats(user_id, username, won, guesses)
    update_leaderboard(user_id, username, won, guesses)

def update_user_stats(user_id, username, won, guesses):
    stats = UserStats.query.filter_by(wordle_user_id=user_id).first()

    if not stats:
        stats = UserStats(
            wordle_user_id=user_id,
            username=username
        )
        db.session.add(stats)

    stats.total_games += 1

    if won:
        stats.total_wins += 1
        stats.avg_guesses = round(
            ((stats.avg_guesses * (stats.total_wins - 1)) + guesses) / stats.total_wins, 2
        )

    db.session.commit()

def update_leaderboard(user_id, username, won, guesses):
    entry = Leaderboard.query.filter_by(wordle_user_id=user_id).first()

    if not entry:
        entry = Leaderboard(
            wordle_user_id=user_id,
            username=username
        )
        db.session.add(entry)

    if won:
        # higher score for winning in fewer guesses
        entry.score = round(entry.score + (10 - guesses), 2)

    db.session.commit()
