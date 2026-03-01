import click
import hashlib
from flask.cli import with_appcontext
from datetime import datetime

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
