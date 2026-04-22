from flask_restful import Resource
from werkzeug.exceptions import NotFound

from statservice import db
from statservice.models import UserStats

class UserStatsResource(Resource):

    def get(self, user_id):
        userstats = UserStats.query.filter_by(wordle_user_id=user_id).first()
        if not userstats:
            raise NotFound(description=f"User not found")
        return userstats.serialize()
