FROM python:3.13-alpine

WORKDIR /opt/wordleGame

RUN pip install supervisor gunicorn

COPY . .
RUN pip install .

COPY supervisor/supervisord.conf /etc/supervisord.conf

EXPOSE 8000

CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]