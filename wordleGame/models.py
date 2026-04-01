"""Database models and schema helpers for the Wordle API."""

from datetime import datetime, time
import click
from flask.cli import with_appcontext

from . import db

class User(db.Model):
    """Represents an API user and their played games."""

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    username = db.Column(db.String(10), nullable=False)

    games = db.relationship(
        "Game",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def serialize(self):
        """Serialize user data to an API response dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "username": self.username
        }

    def deserialize(self, doc):
        """Deserialize payload into the user model."""
        self.username = doc["username"]

    @staticmethod
    def json_schema():
        """Return JSON schema for validating guess payloads."""
        schema = {
            "type": "object",
            "required": ["username"]
        }
        props = schema["properties"] = {}
        props["username"] = {
            "description": "username when user was created",
            "type": "string"
        }
        return schema


class Game(db.Model):
    """Represents a single Wordle game session."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mode = db.Column(db.String(3), nullable = False)
    attempts = db.Column(db.Integer, nullable = False, default=0)
    won = db.Column(db.Boolean, nullable = False, default=False)
    target_word = db.Column(db.String(5))

    user = db.relationship("User", back_populates="games")

    guesses = db.relationship(
        "Guess",
        back_populates="game",
        cascade="all, delete-orphan"
    )

    def serialize(self):
        """Serialize game data to an API response dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mode": self.mode,
            "attempts": self.attempts,
            "won": self.won,
        }

    def deserialize(self, doc):
        """Deserialize payload into mutable game fields."""
        self.user_id = doc["user_id"]
        self.mode = doc["mode"]

    @staticmethod
    def json_schema():
        """Return JSON schema for validating game payloads."""
        schema = {
            "type": "object",
            "required": ["user_id", "mode"]
        }
        props = schema["properties"] = {}
        props["user_id"] = {
            "description": "ID of the user",
            "type": "integer"
        }
        props["mode"] = {
            "description": "'day' or 'inf'",
            "type": "string"
        }
        return schema

class Guess(db.Model):
    """Represents one guess made in a game."""

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    guessed_word = db.Column(db.String(5), nullable = False)
    feedback = db.Column(db.String(5), nullable = False)

    game = db.relationship("Game", back_populates="guesses")

    def serialize(self):
        """Serialize guess data to an API response dictionary."""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "guessed_word": self.guessed_word,
            "feedback": self.feedback
        }

    def deserialize(self, doc):
        """Deserialize payload into mutable guess fields."""
        self.guessed_word = doc["word"]

    @staticmethod
    def json_schema():
        """Return JSON schema for validating guess payloads."""
        schema = {
            "type": "object",
            "required": ["guessed_word"]
        }
        props = schema["properties"] = {}
        props["guessed_word"] = {
            "description": "5 letter word guessed by the player",
            "type": "string"
        }
        return schema

class DailyWord(db.Model):
    """Represents the daily target word entry."""

    date = db.Column(db.DateTime, primary_key=True)
    word = db.Column(db.String(5), nullable = False)

    def serialize(self):
        """Serialize daily-word data to an API response dictionary."""
        return {
            "date": self.date.date().isoformat() if self.date else None,
            "word": self.word
        }

    def deserialize(self, doc):
        """Deserialize date and word payload fields into the model."""
        d = datetime.strptime(doc["date"], "%Y-%m-%d").date()
        self.date = datetime.combine(d, time.min)
        self.word = doc["word"]

    @staticmethod
    def json_schema():
        """Return JSON schema for validating daily-word payloads."""
        return {
            "type": "object",
            "required": ["date", "word"],
            "properties": {
                "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "word": {"type": "string", "minLength": 5, "maxLength": 5}
            },
            "additionalProperties": False
        }

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize database tables."""
    db.create_all()
