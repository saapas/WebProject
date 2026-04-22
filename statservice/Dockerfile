FROM python:3.13-alpine

ENV HOME=/tmp

WORKDIR /opt/statservice

COPY . .
RUN pip install --no-cache-dir setuptools

EXPOSE 8001

CMD ["flask", "--app", "stats_service", "run", "--host", "0.0.0.0", "--port", "8001"]
