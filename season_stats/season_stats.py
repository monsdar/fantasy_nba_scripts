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

NUM_FA_TO_INCLUDE = 100

logging.basicConfig(level=logging.INFO)

def print_to_channel(bot, text):
    if not bot:
        logging.info(text)
    else:
        bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")
        time.sleep(.5)

def get_player_by_playerid(list_of_players, player_id):
    for player in list_of_players:
        if player.playerId == player_id:
            return player
    logging.warn(f"Cannot find player with playerId={player_id}")
    return None

def get_team_score_from_draft(league, all_players):
    team_score = {}
    for draftpick in league.draft:
        # get the team of the draftpick
        curr_team = draftpick.team.team_name
        if not curr_team in team_score:
            team_score[curr_team] = 0.0

        # get the avg score and append it to the teams score
        curr_player = get_player_by_playerid(all_players, draftpick.playerId)
        if not curr_player:
            logging.info(f"Player {draftpick.playerName} from {curr_team} not found")
            continue
        avg_score = curr_player.stats['2023_total']['applied_avg']
        team_score[curr_team] += avg_score

    # return the ranked score, from https://stackoverflow.com/a/613218/199513
    team_score = {k: v for k, v in sorted(team_score.items(), key=lambda item: item[1], reverse=True)}
    return team_score

def get_relative_draft_position(league, all_players):
    ranked_players = {}
    all_players_ranked = sorted(all_players, key=lambda x: x.avg_points, reverse=True)
    for draft_ranking, draftpick in enumerate(league.draft):
        curr_player = get_player_by_playerid(all_players, draftpick.playerId)
        final_ranking = all_players_ranked.index(curr_player)
        ranked_players[draftpick.playerName] = draft_ranking - final_ranking
    ranked_players = {k: v for k, v in sorted(ranked_players.items(), key=lambda item: item[1], reverse=True)}
    return ranked_players

def get_all_players(league):
    all_players = []
    for team in league.teams:
        for player in team.roster:
            all_players.append(player)
    for player in league.free_agents(size=NUM_FA_TO_INCLUDE):
        all_players.append(player)
    return all_players

def get_fa_steals(league, all_players):
    nondrafted_players = []
    ranked_players = sorted(all_players, key=lambda x: x.avg_points, reverse=True)
    for player in ranked_players:
        if player.playerId in [draftpick.playerId for draftpick in league.draft]:
            continue
        nondrafted_players.append(player)
    return nondrafted_players

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
    '''
    parsed_schedule = []
    for index, line in enumerate(raw_schedule.split('\n')):
        if not line.strip():
            continue
        line_elements = line.split(';')
        name = line_elements[0].strip()
        matchup_period = index
        start_date = datetime.strptime(line_elements[1], '%b %d %Y')
        end_date = datetime.strptime(line_elements[2], '%b %d %Y')
        parsed_schedule.append( {'name': name, 'matchup_period': matchup_period, 'start_date': start_date, 'end_date': end_date} )
    return parsed_schedule

def get_scoring_period(given_datetime):
    first_day_of_season = datetime(year=2022, month=10, day=17)
    return (given_datetime - first_day_of_season).days + 1
    
def get_avg_score_from_matchup(lineup, final_score, matchup_date):
    first_scoring_period = get_scoring_period(matchup_date['start_date'])
    last_scoring_period = get_scoring_period(matchup_date['end_date'])
    num_games = 0
    for player in lineup:
        for scoring_period in player.schedule.keys():
            scoring_period = int(scoring_period)
            if scoring_period >= first_scoring_period and scoring_period <= last_scoring_period:
                num_games += 1
    return final_score / num_games

def get_best_avg_score(league):
    matchup_dates = get_matchup_dates()
    best_avg_score = {}
    for matchup_date in matchup_dates:
        logging.info(f"Checking avg score of {matchup_date['name']}")
        matchups = league.box_scores(matchup_period=matchup_date['matchup_period'])
        for matchup in matchups:
            if not matchup.home_team.team_name in best_avg_score:
                best_avg_score[matchup.home_team.team_name] = ("", 0.0)
            if not matchup.away_team.team_name in best_avg_score:
                best_avg_score[matchup.away_team.team_name] = ("", 0.0)

            home_score = get_avg_score_from_matchup(matchup.home_lineup, matchup.home_score, matchup_date)
            away_score = get_avg_score_from_matchup(matchup.away_lineup, matchup.away_score, matchup_date)
            
            if best_avg_score[matchup.home_team.team_name][1] < home_score:
                best_avg_score[matchup.home_team.team_name] = (matchup_date['name'], home_score)
            if best_avg_score[matchup.away_team.team_name][1] < away_score:
                best_avg_score[matchup.away_team.team_name] = (matchup_date['name'], away_score)
    best_avg_score = {k: v for k, v in sorted(best_avg_score.items(), key=lambda item: item[1][1], reverse=True)}
    return best_avg_score

def print_draft_ranking(bot, league, all_players):
    draft_score = get_team_score_from_draft(league, all_players)
    msg = "*Draft Ranking*\n_Wer hat am besten gedrafted? Score setzt sich aus der Avg Score jedes gedrafteten Spielers zusammen:_"
    for index, (team, score) in enumerate(draft_score.items()):
        msg += f"\n  {index+1}. *{team}:* {int(score)}"
    print_to_channel(bot, msg)

def print_draft_steals(bot, relative_draft_positions):
    msg = "*Draft Steals*\n_Spieler die im finalen Ranking weitaus besser als ihre Draft-Position waren:_"
    for player_index in range(5):
        player = list(relative_draft_positions.items())[player_index]
        msg += f"\n  *{player[0]}:* +{player[1]}"
    print_to_channel(bot, msg)

def print_draft_busts(bot, relative_draft_positions):
    msg = "*Draft Busts*\n_Spieler die im finalen Ranking weitaus schlechter als ihre Draft-Position waren:_"
    for player_index in range(5):
        player = list(relative_draft_positions.items())[-(player_index+1)] #access the list backwards
        msg += f"\n  *{player[0]}:* {player[1]}"
    print_to_channel(bot, msg)

def print_fa_steals(bot, fa_steals):
    msg = "*Free Agent Steals*\n_Die besten ungedrafteten Spieler:_"
    points = 0
    for player_index in range(13):
        player = fa_steals[player_index]
        msg += f"\n  *{player.name}:* {player.avg_points}"
        points += player.avg_points
    msg += f"\nAvg Points: {points}"
    print_to_channel(bot, msg)

def print_best_avg_score(bot, best_avg_score):
    msg = "*Beste Score*\n_Das beste Matchup jedes Teams, wenn man die durchschnittliche Score der Spieler zählt:_"
    for index, (team_name, score_data) in enumerate(best_avg_score.items()):
        msg += f"\n  {index+1}. *{team_name}*: {score_data[1]:.2f} _({score_data[0]})_"
    print_to_channel(bot, msg)

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)
    bot = None
    #bot = telegram.Bot(token=BOT_API_KEY)
    
    print_all = False
    if print_all:
        # Gather some data first
        all_players = get_all_players(league)

        # Draft Ranking
        print_draft_ranking(bot, league, all_players)

        # Draft steal and busts
        relative_draft_positions = get_relative_draft_position(league, all_players)
        print_draft_steals(bot, relative_draft_positions)
        print_draft_busts(bot, relative_draft_positions)
        
        # Highest Undrafted Players
        fa_steals = get_fa_steals(league, all_players)
        print_fa_steals(bot, fa_steals)

        # Beste Woche wenn man den Durchschnitt aller Spieler nimmt
        best_avg_score = get_best_avg_score(league)
        print_best_avg_score(bot, best_avg_score)

if __name__ == "__main__":
    main()
