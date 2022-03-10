Collection of scripts to analyze ESPN Fantasy NBA league data

# Setup
* Install latest master of espn-api from https://github.com/cwendt94/espn-api
* Set environment variables:
  * `ESPN_S2`, `SWID`, `LEAGUE_ID` and `LEAGUE_YEAR`: Login details for your league
  * `BOT_API_KEY` and `BOT_CHAT_ID`: API-Key and Chat ID for the telegram bot and channel you'd like to post messages to
  * `INFLUX_SERVER`, `INFLUX_USER`, `INFLUX_PASSWORD`, `INFLUX_DATABASE` and `INFLUX_SERVER`: InfluxDB you'd like to store measures in
* To get the full NBA schedule download scheduleLeagueV2.json from https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json
