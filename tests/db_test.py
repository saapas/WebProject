import os
import tempfile
from datetime import datetime

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, StatementError

from game import create_app, db
from game.models import DailyWord, Game, Guess, User

"""Most of the tests were taken from the course GitHub and slightly modified to fit our purposes"""

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
	return User(created_at=created_at or datetime(2026, 3, 1, 12, 0, 0), username="reika")


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

def test_user_columns_not_nullable(db_handle):
	"""User required columns reject null values."""
	user = _get_user()
	user.username = None
	db_handle.session.add(user)
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


def test_user_serialize_deserialize_and_schema():
	"""User helper methods are exercised for coverage and behavior."""
	user = User(created_at=datetime(2026, 3, 2, 9, 30, 0), username="pena")

	serialized = user.serialize()
	assert serialized["id"] is None
	assert serialized["created_at"] == "2026-03-02T09:30:00"
	assert serialized["username"] == "pena"

	user.deserialize({"username": "pekka"})
	assert user.username == "pekka"

	schema = User.json_schema()
	assert schema["type"] == "object"
	assert schema["required"] == ["username"]
	assert schema["properties"]["username"]["type"] == "string"


def test_game_serialize_deserialize_and_schema():
	"""Game helper methods are exercised for coverage and behavior."""
	game = Game(user_id=5, mode="inf", attempts=2, won=True)

	serialized = game.serialize()
	assert serialized == {
		"id": None,
		"user_id": 5,
		"mode": "inf",
		"attempts": 2,
		"won": True,
	}

	game.deserialize({"user_id": 8, "mode": "day"})
	assert game.user_id == 8
	assert game.mode == "day"

	schema = Game.json_schema()
	assert schema["type"] == "object"
	assert schema["required"] == ["user_id", "mode"]
	assert schema["properties"]["user_id"]["type"] == "integer"
	assert schema["properties"]["mode"]["type"] == "string"


def test_guess_serialize_deserialize_and_schema():
	"""Guess helper methods are exercised for coverage and behavior."""
	guess = Guess(game_id=3, guessed_word="crane", feedback="BGBGB")

	serialized = guess.serialize()
	assert serialized == {
		"id": None,
		"game_id": 3,
		"guessed_word": "crane",
		"feedback": "BGBGB",
	}

	guess.deserialize({"word": "omena"})
	assert guess.guessed_word == "omena"

	schema = Guess.json_schema()
	assert schema["type"] == "object"
	assert schema["required"] == ["guessed_word"]
	assert schema["properties"]["guessed_word"]["type"] == "string"


def test_dailyword_serialize_deserialize_and_schema():
	"""DailyWord helper methods are exercised for coverage and behavior."""
	daily_word = DailyWord(date=datetime(2026, 3, 2, 0, 0, 0), word="slate")

	serialized = daily_word.serialize()
	assert serialized == {"date": "2026-03-02", "word": "slate"}

	daily_word.deserialize({"date": "2026-03-05", "word": "crane"})
	assert daily_word.date == datetime(2026, 3, 5, 0, 0, 0)
	assert daily_word.word == "crane"

	schema = DailyWord.json_schema()
	assert schema["type"] == "object"
	assert schema["required"] == ["date", "word"]
	assert schema["properties"]["date"]["type"] == "string"
	assert schema["properties"]["word"]["type"] == "string"
	assert schema["additionalProperties"] is False
