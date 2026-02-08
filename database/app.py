from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask("app")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False)

    games = db.relationship(
        "Game",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    stats = db.relationship(
        "UserStats",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mode = db.Column(db.String(5), nullable = False)
    attempts = db.Column(db.Integer, nullable = False)
    won = db.Column(db.Boolean, nullable = False)
    lost = db.Column(db.Boolean, nullable = False)

    user = db.relationship("User", back_populates="games")

    guesses = db.relationship(
        "Guess",
        back_populates="game",
        cascade="all, delete-orphan"
    )

class Guess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    guessed_word = db.Column(db.String(5), nullable = False)
    feedback = db.Column(db.String(100), nullable = False)

    game = db.relationship("Game", back_populates="guesses")

class DailyWord(db.Model):
    date = db.Column(db.DateTime, primary_key=True)
    word = db.Column(db.String(5), nullable = False)

class UserStats(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    games_played = db.Column(db.Integer, nullable = False)
    games_won = db.Column(db.Integer, nullable = False)
    win_streak = db.Column(db.Integer, nullable = False)
    avg_guesses = db.Column(db.Float, nullable = False)

    user = db.relationship("User", back_populates="stats")

with app.app_context():
    db.create_all()
