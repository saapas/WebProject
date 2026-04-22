FROM python:3.13-alpine

ENV HOME=/tmp

WORKDIR /opt/stats-service

COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8001

CMD ["flask", "--app", "stats_service", "run", "--host", "0.0.0.0", "--port", "8001"]