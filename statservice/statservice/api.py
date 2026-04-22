"""API blueprint and resource route registration."""

from flask import Blueprint
from flask_restful import Api
from statservice.resources.leaderboard import LeaderboardResource
from statservice.resources.userstats import UserStatsResource


from . import views

api_bp = Blueprint("api", __name__, url_prefix="/stats")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)

"""Resource format was heavily isnpired by the course GitHub"""
"""https://github.com/UniOulu-Ubicomp-Programming-Courses/pwp-sensorhub-example/tree/ex2-project-layout/sensorhub/resources"""
api.add_resource(LeaderboardResource, "/leaderboard")
api.add_resource(UserStatsResource, "/<int:user_id>/")
