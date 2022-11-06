from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from pprint import pprint
import telegram
import time
from datetime import date
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
        return False
    if boxscore1.home_team != boxscore2.home_team:
        return False
    if boxscore1.away_team != boxscore2.away_team:
        return False
    return True

def print_to_channel(bot, text):
    #print(text)
    bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    bot = telegram.Bot(token=BOT_API_KEY)

    # let's check when the first scoring day of the last matchup was
    first_day_of_last_matchup = -1
    last_day_of_last_matchup = -1
    first_matchup = None
    days_since_start = ((date.today() - date(2022, 10, 18)).days)+1 #days since season began
    for current_day in range(days_since_start, days_since_start-20, -1): #do not go backwards more than 20 days, this should never be necessary...
        boxscores = league.box_scores(scoring_period=current_day, matchup_total=False)
        if (not (boxscores[0].winner == "UNDECIDED")) and last_day_of_last_matchup == -1:
            last_day_of_last_matchup = current_day
            first_matchup = boxscores[0]
            print(f"Last day of matchup: {last_day_of_last_matchup}")
        if first_matchup and (not is_same_matchup(boxscores[0], first_matchup)):
            first_day_of_last_matchup = current_day+1
            print(f"First day of matchup: {first_day_of_last_matchup}")
            break

    matchups = {}
    for current_day in range(first_day_of_last_matchup, last_day_of_last_matchup+1):
        boxscores = league.box_scores(scoring_period=current_day, matchup_total=False)
        for boxscore in boxscores:
            matchup_name = f"{boxscore.home_team} versus {boxscore.away_team}"
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
        print_to_channel(bot, text)
        time.sleep(.5)

if __name__ == "__main__":
    main()