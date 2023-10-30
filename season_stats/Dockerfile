FROM python:3.9.15-slim-buster

RUN pip install -U python-telegram-bot==13.15 espn-api

ARG ESPN_S2
ARG SWID
ARG LEAGUE_ID
ARG LEAGUE_YEAR
ARG BOT_API_KEY
ARG BOT_CHAT_ID

ENV ESPN_S2=$ESPN_S2
ENV SWID=$SWID
ENV LEAGUE_ID=$LEAGUE_ID
ENV LEAGUE_YEAR=2023
ENV BOT_API_KEY=$BOT_API_KEY
ENV BOT_CHAT_ID=$BOT_CHAT_ID

COPY ./matchup_prediction.py ./matchup_prediction.py
CMD python ./matchup_prediction.py