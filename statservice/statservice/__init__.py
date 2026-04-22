"""Flask application factory and shared SQLAlchemy instance."""

import os
import atexit
from datetime import datetime
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

    app.cli.add_command(models.init_db_command)
    app.register_blueprint(api.api_bp)

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=lambda: _poll_with_context(app, poll_wordlegame),
            trigger='interval',
            seconds=10,
            next_run_time=datetime.now()
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

    return app

def _poll_with_context(app, poll_fn):
        """Run the poller inside the app context so db is accessible."""
        with app.app_context():
            poll_fn()