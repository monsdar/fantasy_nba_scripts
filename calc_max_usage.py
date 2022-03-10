from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from pprint import pprint
import datetime
import locale
import requests
import json
import os

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])

MATCHUP = "Playoffs 2"
START_DATE = datetime.datetime.now().date()
#START_DATE = datetime.date(year=2022, month=3, day=16)

def main():    
    schedule = read_schedule_from_file()
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    sched_days = get_schedule_by_day(schedule, MATCHUP, START_DATE)

    #drop_players = ["Isaiah Roby", "Immanuel Quickley", "Moritz Wagner"]
    #drop_players = ["OG Anunoby", "Immanuel Quickley"]
    #drop_players = ["OG Anunoby", "Isaiah Roby"]
    #drop_players = ["OG Anunoby", "Moritz Wagner"]
    drop_players = ["OG Anunoby"]

    #get all available teams
    all_teams = set()
    for team_list in sched_days.values():
        all_teams.update(team_list)

    #get my roster and remove the drop_players
    roster = []
    for team in league.standings():
        if not "Biber" in team.team_name:
            continue
        roster = team.roster
        roster = [player for player in roster if not player.name in drop_players]

    schedules = {}
    for pro_team in all_teams:
        if not pro_team in schedules:
            schedules[pro_team] = 0
        schedule = get_team_schedule(sched_days, roster, [pro_team])
        for day, num_entries in schedule.items():
            if num_entries > 10:
                schedule[day] = 10
        schedules[pro_team] = sum(schedule.values())

    pprint(sorted(schedules.items(), key=lambda item: item[1], reverse=True))
    pprint(get_team_schedule(sched_days, roster))

def get_team_schedule(sched_days, players, add_teams=[]):
    schedule = {}
    for day, pro_teams in sched_days.items():
            schedule[day] = 0
            for player in players:
                player_pro_team = player.proTeam
                if "Kyrie Irving" in player.name:
                    player_pro_team = "KYR"
                if player_pro_team in pro_teams:
                    schedule[day] += 1
            for add_player_team in add_teams:
                if add_player_team in pro_teams:
                    schedule[day] += 1
    return schedule

def get_schedule_by_day(schedule, matchup, earliest_start_date):
    team_days = {}
    games = get_gamedates_split_by_weeks(schedule['leagueSchedule']['gameDates'])
    games_this_matchup = games[matchup]
    for day, gamedates in games_this_matchup.items():
        daytime = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        if daytime < earliest_start_date:
            continue
        if not day in team_days:
            team_days[day] = []
        for gamedate in gamedates:
            for game in gamedate['games']:
                #add home_team
                team_code = game['homeTeam']['teamTricode']
                if team_code == 'PHI':
                    team_days[day].append('PHL')
                if team_code == 'PHL':
                    team_days[day].append('PHI')
                if team_code == 'PHX':
                    team_days[day].append('PHO')
                if team_code == 'PHO':
                    team_days[day].append('PHX')
                team_days[day].append(team_code)
                
                #add away_team
                team_code = game['awayTeam']['teamTricode']
                if team_code == 'PHI':
                    team_days[day].append('PHL')
                if team_code == 'PHL':
                    team_days[day].append('PHI')
                if team_code == 'PHX':
                    team_days[day].append('PHO')
                if team_code == 'PHO':
                    team_days[day].append('PHX')
                team_days[day].append(team_code)

                #add team_kyrie
                is_brooklyn_away = game['awayTeam']['teamTricode'] == "BKN"
                is_in_toronto = game['homeTeam']['teamTricode'] == "TOR"
                is_in_nyc = game['homeTeam']['teamTricode'] == "NYK"
                if is_brooklyn_away and not is_in_nyc and not is_in_toronto:
                    team_days[day].append('KYR')
    return team_days
        
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
    Playoffs 1;Mar 14 2022;Mar 27 2022
    Playoffs 2;Mar 28 2022;Apr 10 2022'''
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

def get_games_between(gameDays, start_date, end_date):
    return_gameDays = {}
    for day in range(int((end_date - start_date).days)):
        single_date = start_date + datetime.timedelta(day)

        for gameDate in gameDays:
            curr_date = datetime.datetime.strptime(gameDate['gameDate'], '%m/%d/%Y %I:%M:%S %p')
            if single_date == curr_date:
                date_str = single_date.strftime("%Y-%m-%d")
                if not date_str in return_gameDays:
                    return_gameDays[date_str] = []
                return_gameDays[date_str].append(gameDate)
    return return_gameDays

def read_schedule_from_file(file_path='scheduleLeagueV2.json'):
    f = open(file_path)
    return json.load(f)

def read_schedule_from_url(url='https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json'):
    response = requests.get(url)
    return response.json()

if __name__ == "__main__":
    main()