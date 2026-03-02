import datetime
import json
import os
import tempfile
from flask.testing import FlaskClient
import pytest
from werkzeug.datastructures import Headers

from game import create_app, db
from game.models import User, Game, Guess, DailyWord

TEST_KEY = "verysafetestkey"

@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    os.close(db_fd)
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True,
    }

    app = create_app(config)

    ctx = app.app_context()
    ctx.push()

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.rollback()
    db.session.remove()
    db.drop_all()
    db.engine.dispose()
    ctx.pop()
    os.unlink(db_fname)

def _populate_db():
    
    base_date = datetime.datetime.now().date()
    daily_words_list = ["omena", "bread", "crane", "drink", "eagle"]
    for i, word in enumerate(daily_words_list):
        dw = DailyWord(date=datetime.datetime.combine(base_date + datetime.timedelta(days=i), datetime.datetime.min.time()), word=word)
        db.session.add(dw)

    db.session.commit()

    users = []
    for _ in range(3):
        user = User()
        db.session.add(user)
        users.append(user)

        daily_game = Game(mode="day")
        daily_game.target_word = daily_words_list[0]
        user.games.append(daily_game)

        for i in range(2):
            inf_game = Game(mode="inf")
            inf_game.target_word = daily_words_list[i +1]
            user.games.append(inf_game)

    db.session.commit()

def _get_game_json(user):
    """
    Creates a valid game JSON object to be used for PUT and POST tests.
    """

    return {"user_id": user.id, "mode": "day"}


class TestGameCollection:

    RESOURCE_URL = "/api/games"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 9
        for item in body:
            assert "id" in item
            assert "user_id" in item
            assert "mode" in item
            assert "attempts" in item
            assert "won" in item

    def test_post_valid_request_day(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

    def test_post_valid_request_inf(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid["mode"] = "inf"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

    def test_post_no_daily_word(self, client):
        db.session.query(DailyWord).delete()
        db.session.commit()
        
        user = db.session.query(User).first()
        game_data = {
            "user_id": user.id,
            "mode": "day",
        }
        
        resp = client.post("/api/games", json=game_data)
        assert resp.status_code == 400

    def test_wrong_mediatype(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

    def test_post_missing_field(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid.pop("mode")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_invalid_game_data(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid["mode"] = 99999
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_post_userid_conflict(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid["user_id"] = 999999
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404


class TestGameItem:

    INVALID_URL = "/api/games/gameid/non-game"

    def test_get(self, client):
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.get(url)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert "id" in body
        assert "mode" in body
        assert "attempts" in body
        assert "won" in body
        assert body["id"] == game.id
        assert body["mode"] in ["day", "inf"]
        assert body["attempts"] == 0
        assert body["won"] == False

    def test_get_not_found(self, client):
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put_valid_request(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.put(url, json=valid)
        assert resp.status_code == 204

    def test_put_invalid_game_data(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        nonid = 99999
        url = f"/api/games/{nonid}"
        resp = client.put(url, json=valid)
        assert resp.status_code == 404

    def test_wrong_mediatype(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.put(url, data=json.dumps(valid))
        assert resp.status_code == 415

    def test_put_missing_field(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid.pop("mode")
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.put(url, json=valid)
        assert resp.status_code == 400

    def test_put_userid_conflict(self, client):
        user = db.session.query(User).first()
        valid = _get_game_json(user)
        valid["user_id"] = "blubla"
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.put(url, json=valid)
        assert resp.status_code == 400
    
    def test_delete_game(self, client):
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}"
        resp = client.delete(url)
        assert resp.status_code == 204
        resp = client.get(url)
        assert resp.status_code == 404

    def test_delete_nonexistent_game(self, client):
        resp = client.delete("/api/games/99999")
        assert resp.status_code == 404

class TestGuessCollection:

    def test_get_guesses(self, client):
        game = db.session.query(Game).first()
        if len(game.guesses) == 0:
            client.post(f"/api/games/{game.id}/guesses", json={"guessed_word": "kalja"})
            db.session.refresh(game)
        
        url = f"/api/games/{game.id}/guesses"
        resp = client.get(url)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        if len(body) > 0:
            for guess in body:
                assert "id" in guess
                assert "game_id" in guess
                assert "guessed_word" in guess
                assert "feedback" in guess

                assert guess["game_id"] == game.id
        
        assert len(body) == len(game.guesses)


    def test_post_valid_guess(self, client):
        game = db.session.query(Game).filter_by(mode="day").first()
        url = f"/api/games/{game.id}/guesses"
        resp = client.post(url, json={"guessed_word": "kalja"})
        assert resp.status_code == 201
        body = json.loads(resp.data)
        assert "feedback" in body
        assert len(body["feedback"]) == 5
        updated = db.session.get(Game, game.id)
        assert updated.attempts == 1

    def test_post_winning_guess(self, client):
        game = db.session.query(Game).filter_by(mode="day").first()
        url = f"/api/games/{game.id}/guesses"
        resp = client.post(url, json={"guessed_word": "omena"})
        assert resp.status_code == 201
        updated = db.session.get(Game, game.id)
        assert updated.won is True

    def test_post_too_many_attempts(self, client):
        game = db.session.query(Game).filter_by(mode="day").first()
        url = f"/api/games/{game.id}/guesses"
        for _ in range(6):
            client.post(url, json={"guessed_word": "kalja"})
        resp = client.post(url, json={"guessed_word": "kalja"})
        assert resp.status_code == 400

    def test_post_invalid_length(self, client):
        game = db.session.query(Game).first()
        url = f"/api/games/{game.id}/guesses"
        resp = client.post(url, json={"guessed_word": "abc"})
        assert resp.status_code == 400
    
    def test_post_guess_wrong_type(self, client):
        game = db.session.query(Game).filter_by(mode="day").first()
        url = f"/api/games/{game.id}/guesses"
        resp = client.post(url, json={"guessed_word": 12345})
        assert resp.status_code == 400

    def test_post_already_won(self, client):
        game = db.session.query(Game).filter_by(mode="day").first()
        url = f"/api/games/{game.id}/guesses"
        client.post(url, json={"guessed_word": "omena"})
        resp = client.post(url, json={"guessed_word": "kalja"})
        assert resp.status_code == 400
