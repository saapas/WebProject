FROM python:3.13-alpine

ENV HOME=/tmp
RUN pip install --no-cache-dir setuptools flask flask-sqlalchemy flask-restful apscheduler requests

WORKDIR /opt/statservice

COPY . .
RUN pip install --no-cache-dir setuptools

EXPOSE 8001

CMD ["python", "-m", "flask", "--app", "statservice", "run", "--host", "0.0.0.0", "--port", "8001"]
