from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from pprint import pprint
import telegram
import datetime
import os
import sys

if not 'ESPN_S2' in os.environ:
    print("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])
BOT_API_KEY = os.environ['BOT_API_KEY']
BOT_CHAT_ID = os.environ['BOT_CHAT_ID']

# Testing purposes...
#bot = telegram.Bot(token=BOT_API_KEY)
#bot.send_message(text="Einer noch...", chat_id=BOT_CHAT_ID, parse_mode="Markdown")
#sys.exit(0)

def main():
    action_types = {}
    action_types['DROPPED'] = 'dropped'
    action_types['FA ADDED'] = 'added FA'
    action_types['WAIVER ADDED'] = 'added Waiver'
    action_types['TRADED'] = 'traded'

    bot = telegram.Bot(token=BOT_API_KEY)

    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    activities = league.recent_activity(size=10)
    for activity in activities:
        timepoint = datetime.datetime.fromtimestamp(activity.date/1000.0)
        last_hour = datetime.datetime.now() - datetime.timedelta(hours = 1)
        if timepoint < last_hour:
            continue

        message = "_" + timepoint.strftime("%H:%M:%S") + "_ New Activity:\n"
        for action in activity.actions:
            team = action[0].team_name
            type = action_types[action[1]]
            player = action[2]
            message += f"\* *{team}* {type} *{player}*\n"
        bot.send_message(text=message, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

if __name__ == "__main__":
    main()