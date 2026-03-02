import os
import tempfile
from datetime import datetime
from pathlib import Path
import sys

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, StatementError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game import create_app, db
from game.models import DailyWord, Game, Guess, User


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
	cursor = dbapi_connection.cursor()
	cursor.execute("PRAGMA foreign_keys=ON")
	cursor.close()


@pytest.fixture
def db_handle():
	db_fd, db_fname = tempfile.mkstemp()
	os.close(db_fd)
	config = {
		"SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
		"SQLALCHEMY_TRACK_MODIFICATIONS": False,
		"TESTING": True,
	}

	app = create_app(config)
	ctx = app.app_context()
	ctx.push()
	db.create_all()

	yield db

	db.session.rollback()
	db.drop_all()
	db.session.remove()
	db.engine.dispose()
	ctx.pop()
	os.unlink(db_fname)


def _get_user(created_at=None):
	return User(created_at=created_at or datetime(2026, 3, 1, 12, 0, 0))


def _get_game(mode="daily", attempts=4, won=True):
	return Game(mode=mode, attempts=attempts, won=won)


def _get_guess(guessed_word="crane", feedback="BGBGB"):
	return Guess(guessed_word=guessed_word, feedback=feedback)


def _get_daily_word(date=None, word="slate"):
	return DailyWord(date=date or datetime(2026, 3, 1), word=word)


def test_create_instances_and_relationships(db_handle):
	"""Creates core records and verifies their relationships."""
	user = _get_user()
	game = _get_game()
	guess = _get_guess()
	daily_word = _get_daily_word()

	game.user = user
	guess.game = game

	db_handle.session.add(user)
	db_handle.session.add(game)
	db_handle.session.add(guess)
	db_handle.session.add(daily_word)
	db_handle.session.commit()

	assert User.query.count() == 1
	assert Game.query.count() == 1
	assert Guess.query.count() == 1
	assert DailyWord.query.count() == 1

	db_user = User.query.first()
	db_game = Game.query.first()
	db_guess = Guess.query.first()

	assert db_game.user == db_user
	assert db_guess.game == db_game
	assert db_game in db_user.games
	assert db_guess in db_game.guesses


def test_cascade_delete_user_removes_games_and_guesses(db_handle):
	"""Deleting a user cascades to games and guesses."""
	user = _get_user()
	game = _get_game()
	guess = _get_guess()

	game.user = user
	guess.game = game

	db_handle.session.add_all([user, game, guess])
	db_handle.session.commit()

	db_handle.session.delete(user)
	db_handle.session.commit()

	assert User.query.count() == 0
	assert Game.query.count() == 0
	assert Guess.query.count() == 0


def test_cascade_delete_game_removes_guesses(db_handle):
	"""Deleting a game removes its related guesses."""
	game = _get_game()
	guess = _get_guess()
	guess.game = game

	db_handle.session.add_all([game, guess])
	db_handle.session.commit()

	db_handle.session.delete(game)
	db_handle.session.commit()

	assert Game.query.count() == 0
	assert Guess.query.count() == 0


def test_game_columns_not_nullable(db_handle):
	"""Game required columns reject null values."""
	game = _get_game()
	game.mode = None
	db_handle.session.add(game)
	with pytest.raises(IntegrityError):
		db_handle.session.commit()

	db_handle.session.rollback()

def test_guess_columns_not_nullable(db_handle):
	"""Guess required columns reject null values."""
	guess = _get_guess()
	guess.guessed_word = None
	db_handle.session.add(guess)
	with pytest.raises(IntegrityError):
		db_handle.session.commit()

	db_handle.session.rollback()

	guess = _get_guess()
	guess.feedback = None
	db_handle.session.add(guess)
	with pytest.raises(IntegrityError):
		db_handle.session.commit()


def test_daily_word_columns_and_primary_key(db_handle):
	"""DailyWord enforces non-null word and unique date key."""
	daily_word = _get_daily_word()
	daily_word.word = None
	db_handle.session.add(daily_word)
	with pytest.raises(IntegrityError):
		db_handle.session.commit()

	db_handle.session.rollback()

	same_date = datetime(2026, 3, 2)
	first = _get_daily_word(date=same_date, word="slate")
	second = _get_daily_word(date=same_date, word="cigar")
	db_handle.session.add(first)
	db_handle.session.add(second)
	with pytest.raises(IntegrityError):
		db_handle.session.commit()


def test_user_created_at_type_validation(db_handle):
	"""User.created_at only accepts datetime values."""
	user = _get_user()
	user.created_at = "2026-03-01"
	db_handle.session.add(user)

	with pytest.raises(StatementError):
		db_handle.session.commit()


def test_daily_word_datetime_type_validation(db_handle):
	"""DailyWord.date only accepts datetime values."""
	daily_word = _get_daily_word()
	daily_word.date = "2026-03-01"
	db_handle.session.add(daily_word)

	with pytest.raises(StatementError):
		db_handle.session.commit()
