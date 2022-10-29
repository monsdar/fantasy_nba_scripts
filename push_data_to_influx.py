from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

import datetime
import locale
import requests
import json
import os
import sys
import logging
logging.basicConfig(level=logging.INFO)

if not 'ESPN_S2' in os.environ:
    logging.fatal("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])

INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")

score_types = ['2023_last_7', '2023_last_15', '2023_last_30', '2023', '2022']

def main():
    schedule = read_schedule_from_file()
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    points = []

    logging.info("Read league Activity")
    activities = league.recent_activity(size=0)
    for activity in activities:
        timepoint = datetime.datetime.fromtimestamp(activity.date/1000.0)

        #store the teams in case we have a trade activity and need to know about the other team involved
        team1 = activity.actions[0][0].team_name
        team2 = None
        for action in activity.actions:
            curr_team_name = action[0].team_name
            if curr_team_name != team1:
                team2 = curr_team_name

        for action in activity.actions:
            action_type = "DROPPED"
            if "ADDED" in action[1]:
                action_type = "ADDED"
            points.append({
                    'measurement': 'fantasy_activity',
                    'tags': {
                        'player': action[2],
                        'type': action_type,
                        'fantasy_team': action[0].team_name
                    },
                    "time": timepoint.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fields": {
                        "value": 1 #we need to have a value, so for counting reasons just put 1 into each action
                    }
                })

            #if type==DROPPED and there is another team we have a trade and need to add the given player to team2
            if action_type == "DROPPED" and team2:
                points.append({
                        'measurement': 'fantasy_activity',
                        'tags': {
                            'player': action[2],
                            'type': 'ADDED',
                            'fantasy_team': team2
                        },
                        "time": timepoint.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "fields": {
                        "value": 1 #we need to have a value, so for counting reasons just put 1 into each action
                        }
                    })

    logging.info("Reading data for teams...")
    for team in league.standings():
        logging.info("   ...%s" % team.team_name)
        team_points = get_fantasy_playervalue_points(team.roster, schedule, team.team_name)
        points.extend(team_points)
    
    logging.info("Query a list of all free agents...")
    all_free_agents = league.free_agents(size=0)
    
    logging.info("Reading data for free agents...")
    fa_points = get_fantasy_playervalue_points(all_free_agents, schedule, "Free Agents", skip_scores_below=10.0)
    points.extend(fa_points)

    logging.info("Pushing %s data points to InfluxDB" % len(points))
    influx_client = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    influx_write_api.write(record=points, bucket=INFLUX_BUCKET, org=INFLUX_ORG, time_precision='s')

def get_fantasy_playervalue_points(players, schedule, fantasy_team, skip_scores_below=-100.0):
    points = []
    for player in players:
        for (matchup, games) in get_gamedates_split_by_weeks(schedule['leagueSchedule']['gameDates']).items():
            for score_type in score_types:
                games_per_team = get_num_games_per_team(games)
                score = get_score_for_player(player, score_type, games_per_team)
                #to get a normalized score we assume everyone is playing for the Lakers
                normalized_score = get_score_for_player(player, score_type, games_per_team, overwrite_team='LAL')

                if score < skip_scores_below: #this skips players who are barely productive
                    continue

                points.append({
                        'measurement': 'fantasy_playervalue',
                        'tags': {
                            'player': player.name,
                            'pro_team': player.proTeam,
                            'fantasy_team': fantasy_team,
                            'injury_status': player.injuryStatus,
                            'is_on_ir': (player.lineupSlot == "IR"),
                            'matchup': matchup,
                            'score_type': score_type,
                            'acquisitionType': player.acquisitionType
                        },
                        "time": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "fields": {
                            "score": score,
                            "normalized_score": normalized_score
                        }
                    })
    return points

def get_gamedates_split_by_weeks(gameDays):
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
    Playoffs Full;Mar 6 2023;Mar 26 2023
    Round 1;Mar 6 2023;Mar 12 2023
    Round 2;Mar 13 2023;Mar 19 2023
    Round 3;Mar 20 2023;Mar 26 2023'''
    parsed_schedule = []
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8") #to make sure we can parse English month names like Oct etc
    for line in raw_schedule.split('\n'):
        if not line.strip():
            continue
        line_elements = line.split(';')
        name = line_elements[0].strip()
        start_date = datetime.datetime.strptime(line_elements[1], '%b %d %Y')
        end_date = datetime.datetime.strptime(line_elements[2], '%b %d %Y')
        parsed_schedule.append( {'name': name, 'start_date': start_date, 'end_date': end_date} )

    gameweeks = {}
    for matchup in parsed_schedule:
        gameweeks[matchup['name']] = get_games_between(gameDays, matchup['start_date'], matchup['end_date'])
    return gameweeks

def get_score_for_player(player, score_type, games_per_team, overwrite_team=''):
    if player.proTeam == "FA": #ignore players that aren't playing right now
        return 0.0
    if not score_type in player.stats: #for rookies there's no data for 2022... use 2023 in that case to have something to work with
        score_type = '2023'

    pro_team = player.proTeam
    if overwrite_team:
        pro_team = overwrite_team
    avg_score = player.stats[score_type]['applied_avg']
    return avg_score * games_per_team[pro_team]

def get_num_games_per_team(gameDays):
    teams = {}
    for gameDay in gameDays:
        for game in gameDay['games']:
            home = game['homeTeam']['teamTricode']
            away = game['awayTeam']['teamTricode']
            if not home in teams:
                teams[home] = 0
            if not away in teams:
                teams[away] = 0
            teams[home] += 1
            teams[away] += 1
    #for some reason ESPN shortens some cities differently. Let's copy the nums for those
    teams['PHL'] = teams['PHI']
    teams['PHO'] = teams['PHX']
    return teams

def get_games_between(gameDays, start_date, end_date):
    return_gameDays = []
    for gameDate in gameDays:
        curr_date = datetime.datetime.strptime(gameDate['gameDate'], '%m/%d/%Y %I:%M:%S %p')
        if start_date <= curr_date <= end_date:
            return_gameDays.append(gameDate)
    return return_gameDays

def read_schedule_from_file(file_path='scheduleLeagueV2.json'):
    f = open(file_path)
    return json.load(f)

def read_schedule_from_url(url='https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json'):
    response = requests.get(url)
    return response.json()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(e)
        raise