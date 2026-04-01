FROM python:3.13-alpine

ENV HOME=/tmp

RUN pip install supervisor gunicorn

WORKDIR /opt/wordleGame

COPY . .
RUN pip install .

COPY supervisor/supervisord.conf /etc/supervisord.conf

EXPOSE 8000

CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]