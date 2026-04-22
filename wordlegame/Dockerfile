FROM python:3.13-alpine

ENV HOME=/tmp

RUN pip install --no-cache-dir gunicorn flask flask-sqlalchemy

WORKDIR /opt/wordlegame

COPY . .

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "wordlegame:create_app()"]
