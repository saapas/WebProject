from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from game import db
from game.models import Game, Guess
from game.game_logic import process_guess


class GuessCollection(Resource):

    def get(self, game_id):
        response_data = []
        game = db.session.get(Game, game_id)
        for guess in game.guesses:
            response_data.append(guess.serialize())
        return response_data

    def post(self, game_id):
        if not request.json:
            raise UnsupportedMediaType

        game = db.session.get(Game, game_id)

        try:
            validate(request.json, Guess.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        
        guessed_word = request.json.get("guessed_word")

        try:
            guess = process_guess(game, guessed_word)
            db.session.add(guess)
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid guess")
        except ValueError as e:
            raise BadRequest(description=str(e))

        return guess.serialize(), 201
