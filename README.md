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

## Required components
- Docker
- NGINX
- Gunicorn

## API documentation

The OpenAPI document is included in the repository at `wordlegame/openapi.yaml`.

## Installation (inside a Python virtual environment)
From the project root:

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate it:

PowerShell (Windows):

```bash
.\.venv\Scripts\Activate.ps1
```

3. Install the project and dependencies:

```bash
pip install .
```

## Run the API (development)
From the project root:

```bash
flask --app wordlegame.wordlegame:create_app run --debug
```

Default URLs:
- API entrypoint: `http://127.0.0.1:5000/api/`

## Database setup and population
This API uses SQLite at `instance/wordlegame.db` by default.

### Create tables
From the project root:

```bash
flask --app wordlegame.wordlegame:create_app init-db
```

## Discord Client (Bot)
The repository includes a Discord bot client at `discord-bot/bot.py`.

### What the client does
- Registers a Discord user to an API user
- Creates and plays Wordle games through slash commands
- Restricts users to their own active game
- Shows formatted guess feedback and guess history
- Shows leaderboard and per-user stats from the stats service

### Prerequisites
- Python virtual environment activated
- Discord bot application and token from Discord Developer Portal
- Bot invited to your server with these scopes:
	- `bot`
	- `applications.commands`

### Install client dependencies
From the project root:

```bash
pip install discord.py aiohttp
```

### Run required backend services
You need the game API and stats service running before starting the bot.

1. Run game API (terminal 1):

```bash
flask --app wordlegame.wordlegame:create_app init-db
flask --app wordlegame.wordlegame:create_app run --debug
```

2. Run stats service (terminal 2):

```bash
set WORDLE_API_URL=http://127.0.0.1:5000
flask --app statservice.statservice:create_app init-db
flask --app statservice.statservice:create_app run --debug --port 5001
```

PowerShell version for setting the URL:

```powershell
$env:WORDLE_API_URL="http://127.0.0.1:5000"
```

### Configure and run the bot
Run in a separate terminal (project root):

PowerShell:

```powershell
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN"
$env:WORDLE_API_BASE_URL="http://127.0.0.1:5000"
$env:STAT_API_BASE_URL="http://127.0.0.1:5001"
python .\discord-bot\bot.py
```

### Slash commands
- `/register username:<name>`
	- Registers your Discord account once and maps it to one API user.
- `/newgame mode:day|inf`
	- Starts a new game.
	- User can only have one active game at a time.
	- Daily mode can only be played once per API user.
- `/guess word:<five-letter-word>`
	- Submits guess to your active game automatically.
	- Shows all guesses in order with emoji feedback.
- `/leaderboard`
	- Shows top players from stats service.
- `/stats`
	- Shows your stats.
- `/stats member:@User`
	- Shows another registered member's stats.

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

## Deployment
The API is deployed in a Docker environment.

Deployment stack:
- Docker runs the application in an isolated environment
- Supervisor monitors and controls the Gunicorn process
- Gunicorn runs the Flask application with 3 workers on port 8000
- NGINX works as a reverse proxy and forwards requests to the application server

## Notes
- Packaging is configured through `pyproject.toml` and `MANIFEST.in`.
- This repository currently contains the API service only.
- Client and auxiliary services are not included in this codebase.
