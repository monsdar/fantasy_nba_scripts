from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from pprint import pprint
import telegram
import time
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

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)

    #nba_players = players.get_players()
    #print('Number of players fetched: {}'.format(len(nba_players)))

    # let's check when the first scoring day of the last matchup was
    first_day_of_last_matchup = -1
    last_day_of_last_matchup = -1
    first_matchup = None
    for current_day in range(20): #do not go back more than 20 days... If we reach that limit something odd is happening (Allstar Break?)
        boxscores = league.box_scores(scoring_period=current_day, matchup_total=False)
        if (not (boxscores[0].winner == "UNDECIDED")) and first_day_of_last_matchup == -1:
            first_day_of_last_matchup = current_day
            first_matchup = boxscores[0]
            print(f"First day of matchup: {first_day_of_last_matchup}")
        if first_matchup and (not is_same_matchup(boxscores[0], first_matchup)):
            last_day_of_last_matchup = current_day
            print(f"Last day of matchup: {last_day_of_last_matchup}")
            break

    matchups = {}
    for current_day in range(first_day_of_last_matchup, last_day_of_last_matchup):
        boxscores = league.box_scores(scoring_period=current_day, matchup_total=False)
        for boxscore in boxscores:
            matchup_name = f"{boxscore.home_team} versus {boxscore.away_team}"
            if not matchup_name in matchups.keys():
                matchups[matchup_name] = {}
            if not boxscore.home_team in matchups[matchup_name].keys():
                matchups[matchup_name][boxscore.home_team] = {}
            if not boxscore.away_team in matchups[matchup_name].keys():
                matchups[matchup_name][boxscore.away_team] = {}

            for player in boxscore.home_lineup:
                if not player.name in matchups[matchup_name][boxscore.home_team].keys():
                    matchups[matchup_name][boxscore.home_team][player.name] = 0.0
                if player.points > matchups[matchup_name][boxscore.home_team][player.name]:
                    matchups[matchup_name][boxscore.home_team][player.name] = player.points
            for player in boxscore.away_lineup:
                if not player.name in matchups[matchup_name][boxscore.away_team].keys():
                    matchups[matchup_name][boxscore.away_team][player.name] = 0.0
                if player.points > matchups[matchup_name][boxscore.away_team][player.name]:
                    matchups[matchup_name][boxscore.away_team][player.name] = player.points

    bot = telegram.Bot(token=BOT_API_KEY)

    # Check the Top10 scoring nights:
    text = "*Top10 Leistungen der letzten Woche*"
    bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")
    all_players_ranked = {}
    for matchup in matchups.values():
        for team in matchup.values():
            all_players_ranked.update(team)
    for index, player_name in enumerate(sorted(all_players_ranked, key=all_players_ranked.get, reverse=True)[:10]):
        text = (f"`{index+1:>2}. {player_name:15}: {all_players_ranked[player_name]} Pts`")
        bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")
        time.sleep(.5)
    
    # Calc ranking sleeper-style (sum of best games of each player)
    text = ("*Matchup-Ergebnisse wenn nur die beste Leistung jedes Spielers zählt*\n_Sleeper-Style, Bench + IR werden mitgezählt_")
    bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")
    for matchup_name, matchup in matchups.items():
        scores = []
        for team in matchup.values():
            scores.append(sum(team.values()))
        home_name = list(matchup.keys())[0]
        home_score = int(scores[0])
        away_name = list(matchup.keys())[1]
        away_score = int(scores[1])
        text = (f"`  {home_name.team_name:>20} {home_score:>4} : {away_score:4} {away_name.team_name:20}`")
        bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")
        time.sleep(.5)

if __name__ == "__main__":
    main()