import os
import requests
from statservice import db
from statservice.models import UserStats, Leaderboard, ProcessedGame

WORDLE_API_URL = os.getenv('WORDLE_API_URL', 'https://navigably-phytosociologic-lorraine.ngrok-free.dev')

def poll_wordlegame():
    print(f'[poller] polling')

    try:
        response = requests.get(
            f'{WORDLE_API_URL}/api/games',
            timeout=5
        )

        if response.status_code != 200:
            print(f'[poller] API returned {response.status_code}, skipping')
            return
        
        games = response.json()

        for game in games:
            game_id = game['id']

            already = ProcessedGame.query.filter_by(game_id=game_id).first()
            if already:
                continue

            won = game['won']
            attempts = game['attempts']

            if won or attempts >= 6:
                process_game(game)

                db.session.add(ProcessedGame(game_id=game_id))
                db.session.commit()

        print(f'[poller] processed {len(games)} games')

    except requests.exceptions.ConnectionError:
        print('[poller] could not reach wordle API, will retry next interval')
    except Exception as e:
        print(f'[poller] unexpected error: {e}')

def process_game(game):
    user_id = game['user_id']
    won = game['won']
    attempts = game['attempts']

    update_user_stats(user_id, won, attempts)
    update_leaderboard(user_id, won, attempts)

def update_user_stats(user_id, won, attempts):
    stats = UserStats.query.filter_by(wordle_user_id=user_id).first()
    if not stats:
        stats = UserStats(
            wordle_user_id=user_id,
            total_games=0,
            total_wins=0,
            avg_guesses=0.0
        )
        db.session.add(stats)

    if not won:
        attempts = 10

    stats.total_games = (stats.total_games or 0) + 1
    stats.total_wins = (stats.total_wins or 0) + 1
    stats.avg_guesses = round(
        (((stats.avg_guesses or 0.0) * (stats.total_wins - 1)) + attempts) / stats.total_wins, 2
    )
    db.session.commit()

def update_leaderboard(user_id, won, attempts):
    entry = Leaderboard.query.filter_by(wordle_user_id=user_id).first()
    if not entry:
        entry = Leaderboard(
            wordle_user_id=user_id,
            score=0.0
        )
        db.session.add(entry)

    if not won:
        attempts = 10

    entry.score = round((entry.score or 0.0) + max(1, 10 - attempts), 2)
    db.session.commit()
