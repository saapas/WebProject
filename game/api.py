"""API blueprint and resource route registration."""

from flask import Blueprint
from flask_restful import Api
from game.resources.game import GameCollection, GameItem
from game.resources.guess import GuessCollection
from game.resources.user import UserCollection, UserItem
from game.resources.dailyword import DailyWordCollection, DailyWordItem


from . import views

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)

api.add_resource(GameCollection, "/games")
api.add_resource(GameItem, "/games/<int:game_id>")
api.add_resource(GuessCollection, "/games/<int:game_id>/guesses")
api.add_resource(UserCollection, "/users", endpoint="usercollection")
api.add_resource(UserItem, "/users/<int:user_id>", endpoint="useritem")
api.add_resource(DailyWordCollection, "/dailywords", endpoint="dailywordcollection")
api.add_resource(DailyWordItem, "/dailywords/<string:date>", endpoint="dailyworditem")
