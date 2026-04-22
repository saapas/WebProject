FROM python:3.13-alpine

ENV HOME=/tmp

RUN pip install supervisor gunicorn

WORKDIR /opt/wordlegame

COPY . .
RUN pip install --no-cache-dir setuptools

COPY supervisor/supervisord.conf /etc/supervisord.conf

EXPOSE 8000

CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]
