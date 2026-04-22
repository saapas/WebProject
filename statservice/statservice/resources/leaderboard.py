from flask_restful import Resource

from statservice.statservice.models import Leaderboard

class LeaderboardResource(Resource):

    def get(self):
        response_data = []
        entries = (Leaderboard.query
                   .order_by(Leaderboard.score.desc())
                   .limit(20)
                   .all())
        for entry in entries:
            response_data.append(entry.serialize())
        return response_data
