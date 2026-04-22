from flask_restful import Resource
from werkzeug.exceptions import NotFound

from statservice import db
from statservice.models import UserStats

class UserStatsResource(Resource):

    def get(self, user_id):
        userstats = db.session.get(UserStats, user_id)
        if not userstats:
            raise NotFound(description=f"User not found")
        return userstats.serialize()
