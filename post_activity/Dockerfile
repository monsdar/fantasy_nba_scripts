FROM python:3.9.15-slim-buster

RUN pip install -U python-telegram-bot espn-api

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

COPY ./post_activity_to_telegram.py ./post_activity_to_telegram.py
CMD python ./post_activity_to_telegram.py