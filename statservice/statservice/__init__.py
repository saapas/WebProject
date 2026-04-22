"""Flask application factory and shared SQLAlchemy instance."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()

def create_app(test_config=None):
    """Create and configure the Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "statservice.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    from . import api
    from . import models
    from .poller import poll_wordlegame

    with app.app_context():
        db.create_all()

    app.register_blueprint(api.api_bp)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: _poll_with_context(app, poll_wordlegame),
        trigger='interval',
        seconds=60
    )
    scheduler.start()

    return app

def _poll_with_context(app, poll_fn):
    """Run the poller inside the app context so db is accessible."""
    with app.app_context():
        poll_fn()