from datetime import datetime
import os

from app import (
    app,
    db,
    create_daily_word,
    create_game,
    create_guess,
    create_user,
    create_user_stats,
    init_db,
)


def reset_sqlite_db(db_path: str) -> None:
    if os.path.exists(db_path):
        os.remove(db_path)


def seed_data() -> None:
    with app.app_context():
        init_db()
        user_1 = create_user(datetime(2026, 2, 1, 9, 0, 0), commit=False)
        user_2 = create_user(datetime(2026, 2, 2, 10, 30, 0), commit=False)

        create_user_stats(user_1, 3, 2, 1, 4.3, commit=False)
        create_user_stats(user_2, 2, 1, 0, 5.0, commit=False)

        game_1 = create_game(user_1, "daily", 4, True, False, commit=False)
        game_2 = create_game(user_1, "daily", 6, False, True, commit=False)
        game_3 = create_game(user_2, "daily", 5, True, False, commit=False)

        create_guess(game_1, "crane", "BGBGB", commit=False)
        create_guess(game_1, "slate", "GGGGG", commit=False)
        create_guess(game_2, "adieu", "BBGBB", commit=False)
        create_guess(game_2, "sober", "BGBGY", commit=False)
        create_guess(game_3, "piano", "BGBGB", commit=False)
        create_guess(game_3, "cigar", "GGGGG", commit=False)

        create_daily_word(datetime(2026, 2, 1), "slate", commit=False)
        create_daily_word(datetime(2026, 2, 2), "cigar", commit=False)

        db.session.commit()


if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(__file__), "..", "test.db")
    reset_sqlite_db(os.path.abspath(db_file))
    seed_data()
    print("Database created")
