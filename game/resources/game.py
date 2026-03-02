from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound
import datetime
import random

from game import db
from game.models import Game, User, DailyWord


class GameCollection(Resource):

    def get(self):
        response_data = []
        games = Game.query.all()
        for game in games:
            response_data.append(game.serialize())
        return response_data

    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Game.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user = db.session.get(User, request.json["user_id"])
        if not user:
            raise NotFound(description="User not found")

        game = Game()
        game.deserialize(request.json)
        
        if game.mode == "day":
            today = datetime.datetime.now().date()
            daily_word = db.session.get(DailyWord, datetime.datetime.combine(today, datetime.datetime.min.time()))
            if not daily_word:
                raise BadRequest(description="No daily word for today")
            game.target_word = daily_word.word

        elif game.mode == "inf":
            words = DailyWord.query.all()
            game.target_word = random.choice(words).word

        try:
            db.session.add(game)
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid game data")

        return Response(status=201, headers={
                "Location": url_for("api.gameitem", game_id=game.id)
            })


class GameItem(Resource):

    def get(self, game_id):
        game = db.session.get(Game, game_id)
        if not game:
            raise NotFound(description=f"Game {game_id} not found")
        return game.serialize()

    def put(self, game_id):
        if not request.json:
            raise UnsupportedMediaType

        game = db.session.get(Game, game_id)
        if not game:
            raise NotFound(description=f"Game {game_id} not found")

        try:
            validate(request.json, Game.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        game.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid update")

        return Response(status=204)

    def delete(self, game_id):
        game = db.session.get(Game, game_id)
        if not game:
            raise NotFound(description=f"Game {game_id} not found")
        db.session.delete(game)
        db.session.commit()
        return Response(status=204)
