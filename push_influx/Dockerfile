FROM python:3.9.15-slim-buster

RUN pip install -U espn-api influxdb_client

ARG ESPN_S2
ARG SWID
ARG LEAGUE_ID
ARG LEAGUE_YEAR
ARG INFLUX_TOKEN
ARG INFLUX_ORG
ARG INFLUX_URL
ARG INFLUX_BUCKET

ENV ESPN_S2=$ESPN_S2
ENV SWID=$SWID
ENV LEAGUE_ID=$LEAGUE_ID
ENV LEAGUE_YEAR=2023
ENV INFLUX_TOKEN=$INFLUX_TOKEN
ENV INFLUX_ORG=$INFLUX_ORG
ENV INFLUX_URL=$INFLUX_URL
ENV INFLUX_BUCKET=$INFLUX_BUCKET

#download the schedule from https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json
COPY ./scheduleLeagueV2.json ./scheduleLeagueV2.json
COPY ./push_data_to_influx.py ./push_data_to_influx.py
CMD python ./push_data_to_influx.py