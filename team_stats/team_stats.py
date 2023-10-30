from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
import telegram
import time
from datetime import datetime, timedelta
from pprint import pprint
import logging
import os
import sys
from tabulate import tabulate

if not 'ESPN_S2' in os.environ:
    print("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])
BOT_API_KEY = os.environ['BOT_API_KEY']
BOT_CHAT_ID = os.environ['BOT_CHAT_ID']

STAT_TYPES = []
STAT_TYPES.append("2024_total")
STAT_TYPES.append("2024_last_7")
STAT_TYPES.append("2024_last_15")
STAT_TYPES.append("2024_last_30")

CATS = ["PTS", "BLK", "STL", "AST", "REB", "TO", "3PTM", "FG%", "FT%"]
CATS_TO_IGNORE = ['FGM', 'FGA', 'FTM', 'FTA']

def print_to_channel(bot, text):
    logging.info(text)
    #bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

def filter_roster(player_list):
    filtered_roster = []
    for player in player_list:
        if player.lineupSlot == 'IR':
            continue
        filtered_roster.append(player)
    return filtered_roster

def get_team_from_boxscore(score):
    new_team = {}
    for cat in CATS:
        stat = score[cat]['value']
        new_team[cat] = stat
    return new_team


def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)

    teams = {}
#    for team in league.teams:
#        new_team = {}
#        for cat in CATS:
#            filtered_roster = filter_roster(team.roster)
#            stat = sum([player.stats['2024_last_15']['avg'][cat] if 'avg' in player.stats['2024_last_15'] else 0.0 for player in filtered_roster])
#            new_team[cat] = stat
#        teams[team.team_abbrev] = new_team

    for score in league.box_scores():
        teams[score.home_team.team_abbrev] = get_team_from_boxscore(score.home_stats)
        teams[score.away_team.team_abbrev] = get_team_from_boxscore(score.away_stats)

    avg_team = {}
    for cat in CATS:
        avg_stat = sum([team[cat] for team in teams.values()]) / len(teams)
        avg_team[cat] = avg_stat
    
    table = []
    for cat in CATS:
        if cat in CATS_TO_IGNORE:
            continue
        if cat == 'TO':
            pos_modifier = -1 # Less TOs is better
        else:
            pos_modifier = 1
        opp_value = teams['SC'][cat] #avg_team[cat]
        prv_value = teams['PRV'][cat]
        delta = (prv_value-opp_value)*pos_modifier
        delta_percent = ((prv_value/opp_value)-1)*pos_modifier
        table.append([cat, prv_value, opp_value, delta, delta_percent])

    table.insert(0, ['CAT', 'PRV', 'SC', 'Delta', 'Delta %'])
    floatfmt = ("", ".2f", ".2f", ".2f", ".2%")
    print(tabulate(table, headers='firstrow', numalign="right", tablefmt='fancy_grid', floatfmt=floatfmt))
    sys.exit(0)

if __name__ == "__main__":
    main()
