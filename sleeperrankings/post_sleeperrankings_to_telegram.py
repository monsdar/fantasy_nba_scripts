from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from pprint import pprint
import telegram
import time
from datetime import date, datetime
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

def is_same_matchup(boxscore1, boxscore2):
    if (not boxscore1) or (not boxscore2):
        print("Boxscores == null")
        return False
    if boxscore1.home_team != boxscore2.home_team:
        print(f"HomeTeam Changed: {boxscore1.home_team} != {boxscore2.home_team}")
        return False
    if boxscore1.away_team != boxscore2.away_team:
        print("AwayTeam Changed")
        return False
    return True

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

def get_last_finished_matchup(given_datetime):
    matchup_dates = get_matchup_dates()
    last_matchup = None
    for matchup_date in matchup_dates:
        if matchup_date['end_date'] >= given_datetime:
            break
        last_matchup = matchup_date
    return last_matchup

def print_to_channel(bot, text):
    #print(text)
    bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    bot = telegram.Bot(token=BOT_API_KEY)

    # let's check when the first scoring day of the last matchup was
    last_matchup = get_last_finished_matchup(datetime.now())
    first_day_of_season = datetime(year=2022, month=10, day=17)
    first_day_of_last_matchup = (last_matchup['start_date'] - first_day_of_season).days +1
    last_day_of_last_matchup = (last_matchup['end_date'] - first_day_of_season).days +1
    print(f"Last day of matchup: {last_day_of_last_matchup}")
    print(f"First day of matchup: {first_day_of_last_matchup}")
    #box = league.box_scores(scoring_period=last_day_of_last_matchup, matchup_total=False)
    #print(box[0].home_score)
    #sys.exit(0)

    matchups = {}
    for current_day in range(first_day_of_last_matchup, last_day_of_last_matchup+1): #we need +1 to include the last day of matchup
        print(f"Getting scores for day #{current_day}")
        boxscores = league.box_scores(scoring_period=current_day, matchup_total=False)
        for boxscore in boxscores:
            matchup_name = f"{boxscore.home_team} versus {boxscore.away_team}"
            print(f"   Matchup: {matchup_name}")
            matchup_winner = boxscore.winner
            if not matchup_name in matchups.keys():
                matchups[matchup_name] = {}
                matchups[matchup_name]['teams'] = {}
            matchups[matchup_name]['winner'] = matchup_winner

            if not boxscore.home_team in matchups[matchup_name]['teams'].keys():
                matchups[matchup_name]['teams'][boxscore.home_team] = {}
            if not boxscore.away_team in matchups[matchup_name]['teams'].keys():
                matchups[matchup_name]['teams'][boxscore.away_team] = {}

            for player in boxscore.home_lineup:
                if player.slot_position == "IR" or player.slot_position == "BE":
                    continue
                if not player.name in matchups[matchup_name]['teams'][boxscore.home_team].keys():
                    matchups[matchup_name]['teams'][boxscore.home_team][player.name] = 0.0
                if player.points > matchups[matchup_name]['teams'][boxscore.home_team][player.name]:
                    matchups[matchup_name]['teams'][boxscore.home_team][player.name] = player.points
            for player in boxscore.away_lineup:
                if player.slot_position == "IR" or player.slot_position == "BE":
                    continue
                if not player.name in matchups[matchup_name]['teams'][boxscore.away_team].keys():
                    matchups[matchup_name]['teams'][boxscore.away_team][player.name] = 0.0
                if player.points > matchups[matchup_name]['teams'][boxscore.away_team][player.name]:
                    matchups[matchup_name]['teams'][boxscore.away_team][player.name] = player.points

    # Check the Top10 scoring nights:
    text = "*Top10 Leistungen der letzten Woche*"
    print_to_channel(bot, text)
    all_players_ranked = {}
    for matchup in matchups.values():
        for team in matchup['teams'].values():
            all_players_ranked.update(team)
    for index, player_name in enumerate(sorted(all_players_ranked, key=all_players_ranked.get, reverse=True)[:10]):
        text = (f"{index+1:>2}. {player_name}: {all_players_ranked[player_name]} Pts")
        print_to_channel(bot, text)
        time.sleep(.5)
    
    # Calc ranking sleeper-style (sum of best games of each player)
    text = ("*Matchup-Ergebnisse wenn nur die beste Leistung jedes Spielers zählt*\n_Sleeper-Style, ohne Bench + IR_")
    print_to_channel(bot, text)
    for matchup_name, matchup in matchups.items():
        scores = []
        for team in matchup['teams'].values():
            scores.append(sum(team.values()))
        home_name = list(matchup['teams'].keys())[0]
        home_score = int(scores[0])
        away_name = list(matchup['teams'].keys())[1]
        away_score = int(scores[1])

        is_different_winner = False
        if (matchup['winner'] == 'HOME' and away_score > home_score) or (matchup['winner'] == 'AWAY' and away_score < home_score):
            is_different_winner = True

        text = (f"  {home_name.team_name} {home_score:>4} : {away_score:4} {away_name.team_name}")
        if is_different_winner:
            text = (f"  *{home_name.team_name} {home_score:>4} : {away_score:4} {away_name.team_name}* _(Gewinner ist unterschiedlich!)_")

        if (home_score + away_score) > 0: # <-- there was an issue with the ESPN data on Dec 24th where matchups got mixed up. This if-condition worked around this issue.
            print_to_channel(bot, text)
        time.sleep(.5)

if __name__ == "__main__":
    main()