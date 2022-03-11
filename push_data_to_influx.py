from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from influxdb import InfluxDBClient
import datetime
import locale
import requests
import json
import os
import sys

if not 'ESPN_S2' in os.environ:
    print("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])

INFLUX_SERVER = os.environ['INFLUX_SERVER']
INFLUX_PORT = 8086
INFLUX_USER = os.environ['INFLUX_USER']
INFLUX_PASSWORD = os.environ['INFLUX_PASSWORD']
INFLUX_DATABASE = os.environ['INFLUX_DATABASE']

score_types = ['2022_last_7', '2022_last_15', '2022_last_30', '2022', '2021']

def main():    
    #influx_client = InfluxDBClient(INFLUX_SERVER, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD, INFLUX_DATABASE)
    #influx_client.delete_series(INFLUX_DATABASE, 'fantasy_playervalue', {})
    #sys.exit()

    schedule = read_schedule_from_file()
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    points = []

    print("Read league Activity")
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

    print("Reading data for teams...")
    for team in league.standings():
        print("   ...%s" % team.team_name)
        team_points = get_fantasy_playervalue_points(team.roster, schedule, team.team_name)
        points.extend(team_points)
    
    print("Query a list of all free agents...")
    all_free_agents = league.free_agents(size=0)
    
    print("Reading data for free agents...")
    fa_points = get_fantasy_playervalue_points(all_free_agents, schedule, "Free Agents", skip_scores_below=10.0)
    points.extend(fa_points)

    print("Pushing %s data points to InfluxDB" % len(points))
    influx_client = InfluxDBClient(INFLUX_SERVER, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD, INFLUX_DATABASE)
    influx_client.write_points(points, time_precision='s')

def get_fantasy_playervalue_points(players, schedule, fantasy_team, skip_scores_below=-100.0):
    points = []
    for player in players:
        for (matchup, games) in get_gamedates_split_by_weeks(schedule['leagueSchedule']['gameDates']).items():
            for score_type in score_types:
                games_per_team = get_num_games_per_team(games)
                games_per_team.update(get_num_games_for_team_kyrie(games))
                score = get_score_for_player(player, score_type, games_per_team)
                #to get a normalized score we assume everyone is playing for the Warriors
                normalized_score = get_score_for_player(player, score_type, games_per_team, overwrite_team='GSW')

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
#    raw_schedule = '''
#    Matchup 1;Oct 19 2021;Oct 24 2021
#    Matchup 2;Oct 25 2021;Oct 31 2021
#    Matchup 3;Nov 1 2021;Nov 7 2021
#    Matchup 4;Nov 8 2021;Nov 14 2021
#    Matchup 5;Nov 15 2021;Nov 21 2021
#    Matchup 6;Nov 22 2021;Nov 28 2021
#    Matchup 7;Nov 29 2021;Dec 5 2021
#    Matchup 8;Dec 6 2021;Dec 12 2021
#    Matchup 9;Dec 13 2021;Dec 19 2021
#    Matchup 10;Dec 20 2021;Dec 26 2021
#    Matchup 11;Dec 27 2021;Jan 2 2022
#    Matchup 12;Jan 3 2022;Jan 9 2022
#    Matchup 13;Jan 10 2022;Jan 16 2022
#    Matchup 14;Jan 17 2022;Jan 23 2022
#    Matchup 15;Jan 24 2022;Jan 30 2022
    raw_schedule = '''
    Matchup 16;Jan 31 2022;Feb 6 2022
    Matchup 17;Feb 7 2022;Feb 13 2022
    Matchup 18;Feb 14 2022;Feb 27 2022
    Matchup 19;Feb 28 2022;Mar 6 2022
    Matchup 20;Mar 7 2022;Mar 13 2022
    ROS;Feb 7 2022;Mar 13 2022
    Playoffs 1;Mar 14 2022;Mar 27 2022
    Playoffs 2;Mar 28 2022;Apr 10 2022
    Playoffs Full;Mar 14 2022;Apr 10 2022'''
#    raw_schedule = '''
#    Playoffs 1;Mar 14 2022;Mar 27 2022
#    Playoffs 2;Mar 28 2022;Apr 10 2022
#    Playoffs Full;Mar 14 2022;Apr 10 2022'''
    parsed_schedule = []
    locale.setlocale(locale.LC_TIME, "en_US") #to make sure we can parse English month names like Oct etc
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
    if "Kyrie Irving" in player.name:
        player.proTeam = "KYR"
    if not score_type in player.stats: #for rookies there's no data for 2021... use 2022 in that case to have something to work with
        score_type = '2022'

    pro_team = player.proTeam
    if overwrite_team:
        pro_team = overwrite_team
    avg_score = player.stats[score_type]['applied_avg']
    return avg_score * games_per_team[pro_team]

def get_num_games_for_team_kyrie(gameDays):
    teams = {}
    kyrie_count = 0
    for gameDay in gameDays:
        for game in gameDay['games']:
            is_brooklyn_away = game['awayTeam']['teamTricode'] == "BKN"
            is_in_toronto = game['homeTeam']['teamTricode'] == "TOR"
            is_in_nyc = game['homeTeam']['teamTricode'] == "NYK"
            if is_brooklyn_away and not is_in_toronto and not is_in_nyc:
                kyrie_count += 1
    teams['KYR'] = kyrie_count
    return teams

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
    main()