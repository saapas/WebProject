# Wordle Game API

This project is a Flask + Flask-RESTful API for a Wordle-style game.

## Group information
- Samuel Palovaara, samuel.palovaara@student.oulu.fi
- Toni Makkonen, Toni.Makkonen@student.oulu.fi
- Eeli Tavaststjerna, eeli.tavaststjerna@student.oulu.fi

## Tech stack
- Python 3.11+
- Flask
- Flask-SQLAlchemy
- Flask-RESTful
- SQLite 3

## Install (project root)
1. Install package and runtime dependencies:

```bash
pip install .
```

2. Install dependecies:

```bash
pip install -r requirements.txt
```

## Run the API (development)
From the project root:

```bash
flask --app game:create_app run --debug
```

Default URL:
- API entrypoint: `http://127.0.0.1:5000/api/`

## Database setup and population
This API uses SQLite at `instance/wordlegame.db` by default.

### Create tables
From the project root:

```bash
flask --app game:create_app init-db
```

### Populate daily words (required for `mode="day"` game creation)
You can add daily words via API:

PowerShell (Windows):

```bash
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/dailywords" -ContentType "application/json" -Body '{"date":"2026-03-02","word":"crane"}'
```

## Run tests
From the project root:

```bash
pytest -q
```

## Run coverage
From the project root:

```bash
pytest tests/db_test.py --cov=game.models --cov-report=term-missing
```

```bash
pytest --cov=game --cov-report=term-missing
```

## Notes
- Packaging is configured through `pyproject.toml` and `MANIFEST.in`.
- This repository currently contains the API service only.
- Client and auxiliary services are not included in this codebase.
