FROM python:3.13-alpine
WORKDIR /opt/game
COPY . .
RUN pip install .
RUN pip install gunicorn supervisor
COPY supervisor/supervisord.conf /etc/supervisord.conf
CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]