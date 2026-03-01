from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from game import db
from game.models import Game, User
from game.game_logic import get_word


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

        user = User.query.get(request.json["user_id"])
        if not user:
            raise NotFound(description="User not found")

        game = Game()
        game.deserialize(request.json)

        try:
            game.target_word = get_word(game)
            db.session.add(game)
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid game data")

        return Response(status=201, headers={
                "Location": url_for("api.gameitem", game_id=game.id)
            })


class GameItem(Resource):

    def get(self, game_id):
        game = Game.query.get_or_404(game_id)
        return game.serialize()

    def put(self, game_id):
        if not request.json:
            raise UnsupportedMediaType

        game = Game.query.get_or_404(game_id)

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
        game = Game.query.get_or_404(game_id)
        db.session.delete(game)
        db.session.commit()
        return Response(status=204)
