"""Database models and schema helpers for the stats-service Auxiliary service for the Wordle API."""

from datetime import datetime, time
from flask.cli import with_appcontext

from .. import db

class Leaderboard(db.Model):
    """Represents a leaderboard entry"""

    id = db.Column(db.Integer, primary_key=True)
    wordle_user_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(10), nullable=False)
    score = db.Column(db.Float, default=0.0)

    def serialize(self):
        """Serialize leaderboard data to an API response dictionary."""
        return {
            "id": self.id,
            "wordle_user_id": self.wordle_user_id,
            "username": self.username,
            "score": self.score
        }

class UserStats(db.Model):
    """Represents an API users statistics"""

    id = db.Column(db.Integer, primary_key=True)
    wordle_user_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(10), nullable=False)
    total_games = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    avg_guesses = db.Column(db.Float, default=0.0)

    def serialize(self):
        """Serialize UserStats data to an API response dictionary."""
        return {
            "id": self.id,
            "wordle_user_id": self.wordle_user_id,
            "username": self.username,
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "avg_guesses": self.avg_guesses
        }
