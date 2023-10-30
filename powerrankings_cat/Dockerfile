FROM python:3.12.0-slim-bullseye

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
ENV LEAGUE_YEAR=$LEAGUE_YEAR
ENV BOT_API_KEY=$BOT_API_KEY
ENV BOT_CHAT_ID=$BOT_CHAT_ID

COPY ./post_powerrankings_to_telegram.py ./post_powerrankings_to_telegram.py
CMD python ./post_powerrankings_to_telegram.py