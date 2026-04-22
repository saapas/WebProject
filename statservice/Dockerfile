FROM python:3.13-alpine

ENV HOME=/tmp

RUN pip install --no-cache-dir \
    flask flask-sqlalchemy flask-restful apscheduler requests gunicorn

WORKDIR /opt/statservice

COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8001

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8001", "statservice:create_app()"]
