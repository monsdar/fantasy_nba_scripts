from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from tabulate import tabulate
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

score_types = ['2022_last_7', '2022_last_15', '2022_last_30', '2022', '2021']

def main():    
    schedule = read_schedule_from_file()
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    
    print("Read current matchups...")
    curr_week = 20
    curr_scoreboard = league.scoreboard(curr_week)
    while not curr_scoreboard[0].winner == 'UNDECIDED':
        curr_week += 1
        curr_scoreboard = league.scoreboard(curr_week)
    team_scores = []
    for match in curr_scoreboard:
        team_scores.append({'team': match.home_team, 'curr_score': int(match.home_final_score) })
        team_scores.append({'team': match.away_team, 'curr_score': int(match.away_final_score) })

    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = datetime.datetime.strptime('Mar 13 2022', '%b %d %Y')
    all_gameDays = schedule['leagueSchedule']['gameDates']
    games_left = get_games_between(all_gameDays, today, end_date)
    games_per_team = get_num_games_per_team(games_left)
    games_per_team.update(get_num_games_for_team_kyrie(games_left))

    for team_score in team_scores:
        team_score['final_score_7'] = team_score['curr_score']
        team_score['final_score_15'] = team_score['curr_score']
        team_score['final_score_30'] = team_score['curr_score']
        for player in team_score['team'].roster:
            if player.injuryStatus == "OUT":
                continue
            if player.lineupSlot == "IR":
                continue
            score = get_score_for_player(player, '2022_last_7', games_per_team)
            team_score['final_score_7'] += int(score)
            score = get_score_for_player(player, '2022_last_15', games_per_team)
            team_score['final_score_15'] += int(score)
            score = get_score_for_player(player, '2022_last_30', games_per_team)
            team_score['final_score_30'] += int(score)
    
    tab_headers = ['Team', 'Current', 'Final L7', 'Final L15', 'Final L30']
    tab_rows = []
    for team_score in team_scores:
        tab_rows.append([team_score['team'].team_name, team_score['curr_score'], team_score['final_score_7'], team_score['final_score_15'], team_score['final_score_30']])
    print(tabulate(tab_rows, headers=tab_headers))



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
    Playoffs Full;Mar 14 2022;Apr 10 2022
    '''
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
    if not pro_team in games_per_team:
        return 0.0
    else:
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
    if 'PHI' in teams:
        teams['PHL'] = teams['PHI']
    if 'PHX' in teams:
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