# PWP SPRING 2026
# PROJECT NAME
# Group information
* Student 1. Samuel Palovaara, samuel.palovaara@student.oulu.fi
* Student 2. Toni  Makkonen, Toni.Makkonen@student.oulu.fi
* Student 3. Eeli Tavaststjerna eeli.tavaststjerna@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__

## Dependencies
- Python 3.11+
- SQLite 3
- requirements.txt

## Database
- SQLite 3

### Generate the populated database using the script
1. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
2. Run the seed script from the project root:
	```bash
	python database/seed_db.py
	```

## ORM Models and Functions
The ORM models and helper functions are defined in [database/app.py](database/app.py). This includes:
- Models: User, Game, Guess, DailyWord, UserStats
- Helper functions: init_db(), create_user(), create_game() etc.

## Scripts Used to Generate the Database
- Seed script: [database/seed_db.py](database/seed_db.py)


