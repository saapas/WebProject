"""API blueprint and resource route registration."""

from flask import Blueprint
from flask_restful import Api
from statservice.resources.leaderboard import Leaderboard
from statservice.resources.userstats import UserStats


from . import views

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)

"""Resource format was heavily isnpired by the course GitHub"""
"""https://github.com/UniOulu-Ubicomp-Programming-Courses/pwp-sensorhub-example/tree/ex2-project-layout/sensorhub/resources"""
api.add_resource(Leaderboard, "/leaderboard")
api.add_resource(UserStats, "/users/<int:user_id>/stats")
