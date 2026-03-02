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

class TestUserCollection:
    RESOURCE_URL = "/api/users"

    def test_get_users(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert isinstance(body, list)
        assert len(body) >= 3
        for u in body:
            assert "id" in u
            assert "created_at" in u

    def test_post_user_valid(self, client):
        resp = client.post(self.RESOURCE_URL, json={})
        assert resp.status_code == 201
        assert "Location" in resp.headers
        # Location should point to created user
        loc = resp.headers["Location"]
        assert "/api/users/" in loc or loc.endswith("/api/users") is False

    def test_post_user_wrong_mediatype(self, client):
        # No JSON => UnsupportedMediaType (415)
        resp = client.post(self.RESOURCE_URL, data="{}")
        assert resp.status_code == 415


class TestUserItem:
    def test_get_user(self, client):
        user = db.session.query(User).first()
        resp = client.get(f"/api/users/{user.id}")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["id"] == user.id
        assert "created_at" in body

    def test_get_user_not_found(self, client):
        resp = client.get("/api/users/999999")
        assert resp.status_code == 404

    def test_put_user_valid(self, client):
        user = db.session.query(User).first()
        resp = client.put(f"/api/users/{user.id}", json={})
        assert resp.status_code == 204

    def test_put_user_wrong_mediatype(self, client):
        user = db.session.query(User).first()
        resp = client.put(f"/api/users/{user.id}", data="{}")
        assert resp.status_code == 415

    def test_delete_user(self, client):
        user = db.session.query(User).first()
        resp = client.delete(f"/api/users/{user.id}")
        assert resp.status_code == 204
        resp2 = client.get(f"/api/users/{user.id}")
        assert resp2.status_code == 404

class TestDailyWordCollection:
    RESOURCE_URL = "/api/dailywords"

    def test_get_dailywords(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert isinstance(body, list)
        assert len(body) >= 5
        for dw in body:
            assert "date" in dw
            assert "word" in dw

    def test_post_dailyword_valid(self, client):
        # create a new date not in seed (far future)
        date_str = (datetime.datetime.now().date() + datetime.timedelta(days=30)).isoformat()
        resp = client.post(self.RESOURCE_URL, json={"date": date_str, "word": "kissa"})
        assert resp.status_code == 201
        assert "Location" in resp.headers

        # verify it can be fetched
        resp2 = client.get(f"/api/dailywords/{date_str}")
        assert resp2.status_code == 200
        body2 = json.loads(resp2.data)
        assert body2["date"] == date_str
        assert body2["word"] == "kissa"

    def test_post_dailyword_invalid_date(self, client):
        resp = client.post(self.RESOURCE_URL, json={"date": "bad-date", "word": "kissa"})
        assert resp.status_code == 400

    def test_post_dailyword_wrong_mediatype(self, client):
        resp = client.post(self.RESOURCE_URL, data='{"date":"2026-01-01","word":"kissa"}')
        assert resp.status_code == 415


class TestDailyWordItem:
    def test_get_dailyword(self, client):
        date_str = datetime.datetime.now().date().isoformat()
        resp = client.get(f"/api/dailywords/{date_str}")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["date"] == date_str
        assert "word" in body
        assert len(body["word"]) == 5

    def test_get_dailyword_bad_date(self, client):
        resp = client.get("/api/dailywords/not-a-date")
        assert resp.status_code == 400

    def test_get_dailyword_not_found(self, client):
        resp = client.get("/api/dailywords/2099-01-01")
        assert resp.status_code == 404

    def test_put_dailyword_valid(self, client):
        date_str = datetime.datetime.now().date().isoformat()
        resp = client.put(f"/api/dailywords/{date_str}", json={"date": date_str, "word": "kissa"})
        assert resp.status_code == 204

        # verify updated
        resp2 = client.get(f"/api/dailywords/{date_str}")
        assert resp2.status_code == 200
        body2 = json.loads(resp2.data)
        assert body2["word"] == "kissa"

    def test_put_dailyword_body_date_mismatch(self, client):
        date_str = datetime.datetime.now().date().isoformat()
        resp = client.put(f"/api/dailywords/{date_str}", json={"date": "2020-01-01", "word": "kissa"})
        assert resp.status_code == 400

    def test_put_dailyword_wrong_mediatype(self, client):
        date_str = datetime.datetime.now().date().isoformat()
        resp = client.put(f"/api/dailywords/{date_str}", data='{"date":"2026-01-01","word":"kissa"}')
        assert resp.status_code == 415

    def test_delete_dailyword(self, client):
        date_str = datetime.datetime.now().date().isoformat()
        resp = client.delete(f"/api/dailywords/{date_str}")
        assert resp.status_code == 204
        resp2 = client.get(f"/api/dailywords/{date_str}")
        assert resp2.status_code == 404

    def test_delete_dailyword_bad_date(self, client):
        resp = client.delete("/api/dailywords/not-a-date")
        assert resp.status_code == 400