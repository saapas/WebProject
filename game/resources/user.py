from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType

from game import db
from game.models import User


class UserCollection(Resource):

    def get(self):
        response_data = []
        users = User.query.all()
        for user in users:
            response_data.append(user.serialize())
        return response_data

    def post(self):
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user = User()
        user.deserialize(request.json)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid user data")

        return Response(status=201, headers={
            "Location": url_for("api.useritem", user_id=user.id)
        })


class UserItem(Resource):

    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound(description=f"User not found")
        return user.serialize()

    def put(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound(description="User not found")

        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid update")

        return Response(status=204)

    def delete(self, user_id):
        user = db.session.get(User, user_id)
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
