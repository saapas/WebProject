from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType

from game import db
from game.models import DailyWord
from datetime import datetime, time


def parse_date(date_str: str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return datetime.combine(d, time.min)


class DailyWordCollection(Resource):

    def get(self):
        response_data = []
        dailywords = DailyWord.query.all()
        for dw in dailywords:
            response_data.append(dw.serialize())
        return response_data

    def post(self):
        try:
            validate(request.json, DailyWord.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        dw = DailyWord()

        dw.deserialize(request.json)

        try:
            db.session.add(dw)
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid dailyword data")

        return Response(status=201, headers={
            "Location": url_for("api.dailyworditem", date=dw.date.date().isoformat())
        })


class DailyWordItem(Resource):

    def get(self, date):
        try:
            dt = parse_date(date)
        except ValueError:
            raise BadRequest(description="Invalid date")

        dw = db.session.get(DailyWord, dt)
        if not dw:
            raise NotFound(description="DailyWord not found")
            
        return dw.serialize()

    def put(self, date):
        try:
            dt = parse_date(date)
        except ValueError:
            raise BadRequest(description="Invalid date")

        dw = db.session.get(DailyWord, dt)

        try:
            validate(request.json, DailyWord.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        if request.json.get("date") != date:
            raise BadRequest(description="date in body must match URL")


        dw.deserialize(request.json)

        try:
            db.session.commit()
        except IntegrityError:
            raise BadRequest(description="Invalid update")

        return Response(status=204)

    def delete(self, date):
        try:
            dt = parse_date(date)
        except ValueError:
            raise BadRequest(description="Invalid date")

        dw = db.session.get(DailyWord, dt)
        db.session.delete(dw)
        db.session.commit()
        return Response(status=204)
