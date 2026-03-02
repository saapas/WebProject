import click
from flask.cli import with_appcontext
from datetime import datetime, time

from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    games = db.relationship(
        "Game",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def serialize(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def deserialize(self, doc):
        return self

    @staticmethod
    def json_schema():
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }


class Game(db.Model):
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
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mode": self.mode,
            "attempts": self.attempts,
            "won": self.won,
        }

    def deserialize(self, doc):
        self.user_id = doc["user_id"]
        self.mode = doc["mode"]

    @staticmethod
    def json_schema():
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
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    guessed_word = db.Column(db.String(5), nullable = False)
    feedback = db.Column(db.String(5), nullable = False)

    game = db.relationship("Game", back_populates="guesses")

    def serialize(self):
        return {
            "id": self.id,
            "game_id": self.game_id,
            "guessed_word": self.guessed_word,
            "feedback": self.feedback
        }

    def deserialize(self, doc):
        self.guessed_word = doc["word"]

    @staticmethod
    def json_schema():
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
    date = db.Column(db.DateTime, primary_key=True)
    word = db.Column(db.String(5), nullable = False)

    def serialize(self):
        return {
            "date": self.date.date().isoformat() if self.date else None,
            "word": self.word
        }

    def deserialize(self, doc):
        # doc["date"] muodossa "YYYY-MM-DD"
        d = datetime.strptime(doc["date"], "%Y-%m-%d").date()
        self.date = datetime.combine(d, time.min)
        self.word = doc["word"]

    @staticmethod
    def json_schema():
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
    db.create_all()
