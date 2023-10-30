from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
import telegram
import time
from datetime import datetime, timedelta
from pprint import pprint
import logging
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

def print_to_channel(bot, text):
    logging.info(text)
    #bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

def get_matchup_dates():
    raw_schedule = '''
    Matchup 1;Oct 17 2022;Oct 23 2022
    Matchup 2;Oct 24 2022;Oct 30 2022
    Matchup 3;Oct 31 2022;Nov 6 2022
    Matchup 4;Nov 7 2022;Nov 13 2022
    Matchup 5;Nov 14 2022;Nov 20 2022
    Matchup 6;Nov 21 2022;Nov 27 2022
    Matchup 7;Nov 28 2022;Dec 4 2022
    Matchup 8;Dec 5 2022;Dec 11 2022
    Matchup 9;Dec 12 2022;Dec 18 2022
    Matchup 10;Dec 19 2022;Dec 25 2022
    Matchup 11;Dec 26 2022;Jan 1 2023
    Matchup 12;Jan 2 2023;Jan 8 2023
    Matchup 13;Jan 9 2023;Jan 15 2023
    Matchup 14;Jan 16 2023;Jan 22 2023
    Matchup 15;Jan 23 2023;Jan 29 2023
    Matchup 16;Jan 30 2023;Feb 5 2023
    Matchup 17;Feb 6 2023;Feb 12 2023
    Matchup 18;Feb 13 2023;Feb 26 2023
    Matchup 19;Feb 27 2023;Mar 5 2023
    Playoffs Round 1;Mar 6 2023;Mar 12 2023
    Playoffs Round 2;Mar 13 2023;Mar 19 2023
    Playoffs Round 3;Mar 20 2023;Mar 26 2023
    Playoffs Full;Mar 6 2023;Mar 26 2023'''
    parsed_schedule = []
    for line in raw_schedule.split('\n'):
        if not line.strip():
            continue
        line_elements = line.split(';')
        name = line_elements[0].strip()
        start_date = datetime.strptime(line_elements[1], '%b %d %Y')
        end_date = datetime.strptime(line_elements[2], '%b %d %Y')
        parsed_schedule.append( {'name': name, 'start_date': start_date, 'end_date': end_date} )
    return parsed_schedule

def get_scoring_period(given_datetime):
    first_day_of_season = datetime(year=2022, month=10, day=17)
    return (given_datetime - first_day_of_season).days + 1

def get_current_matchup(given_datetime):
    matchup_dates = get_matchup_dates()
    current_matchup = None
    for matchup_date in matchup_dates:
        if matchup_date['start_date'] <= given_datetime and matchup_date['end_date'] >= given_datetime:
            current_matchup = matchup_date
            break
    return current_matchup

def get_num_games(player, scoring_period_start, scoring_period_end):
    num_games = 0
    for index in range(scoring_period_start, scoring_period_end+1):
        if str(index) in player.schedule:
            num_games+=1
    return num_games

def get_avg_score(lineup, matchup_player, score_type='2023_last_7'):
    for player in lineup:
        if player.playerId == matchup_player.playerId:
            if player.injuryStatus == "OUT":
                return 0.0
            else:
                return player.stats[score_type]['applied_avg']
    raise Exception('Player not found!')

def debug(player):
    print(f"  Player: {player.name}, len(schedule): {len(player.schedule)}, projected_total_points: {player.projected_total_points}")

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    curr_matchup = get_current_matchup(datetime.now())
    curr_scoring_period = get_scoring_period(datetime.now())
    last_day_of_last_matchup = get_scoring_period(curr_matchup['end_date'])

    score_types = [
        '2023_last_7',
        #'2023_last_15',
        #'2023_last_30',
    ]

    for score_type in score_types:
        print(f"Score Type: {score_type}")
        
        for matchup in league.box_scores():
            score_home_left = 0
            #print(f"    {matchup.home_team.team_name}:")
            for player in matchup.home_lineup:
                num_games_left = get_num_games(player, curr_scoring_period, last_day_of_last_matchup)
                avg_score_player = get_avg_score(matchup.home_team.roster, player, score_type)
                total_score_player = num_games_left * avg_score_player
                #print(f"      - {player.name}: {total_score_player}")
                score_home_left += total_score_player

            score_away_left = 0
            #print(f"    {matchup.away_team.team_name}:")
            for player in matchup.away_lineup:
                num_games_left = get_num_games(player, curr_scoring_period, last_day_of_last_matchup)
                avg_score_player = get_avg_score(matchup.away_team.roster, player, score_type)
                total_score_player = num_games_left * avg_score_player
                #print(f"      - {player.name}: {total_score_player}")
                score_away_left += total_score_player

            full_home_score = int(score_home_left+matchup.home_score)
            full_away_score = int(score_away_left+matchup.away_score)

            print(f"  {matchup.home_team.team_name} {full_home_score} - {full_away_score} {matchup.away_team.team_name}")

if __name__ == "__main__":
    main()

data = '''
Freitag
* Gryffindor Ganoven 1143 - 1240 Steglitz Cardinals
* Furious Aardvarks 1005 - 1212 Tacko Falls
* Ice Jrue 1490 - 1207 Uesen Celtics
* Can‘t Blazemore 1075 - 777 CrashTest Dummies
* Wilmersdorfer  Witwen 870 - 919 Ostertimke City Thunder

Samstag
* Gryffindor Ganoven 1080 - 1252 Steglitz Cardinals
* Furious Aardvarks 1068 - 1246 Tacko Falls
* Ice Jrue 1456 - 1142 Uesen Celtics
* Can‘t Blazemore 1092 - 796 CrashTest Dummies
* Wilmersdorfer  Witwen 828 - 959 Ostertimke City Thunder
'''