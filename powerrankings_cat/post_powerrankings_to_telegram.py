
from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
import logging
import os
import sys
import telegram
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")

if not 'ESPN_S2' in os.environ:
    logging.fatal("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])
BOT_API_KEY = os.environ['BOT_API_KEY']
BOT_CHAT_ID = os.environ['BOT_CHAT_ID']

START_WEEK = 1 #this is to not gather data from the whole season in the later stages of the season
NUM_WEEKS_TO_CALC = 4
CATS = ["PTS", "BLK", "STL", "AST", "REB", "TO", "3PTM", "FG%", "FT%"]

def print_to_channel(bot, text):
    logging.info(text)
    bot.send_message(text=text, chat_id=BOT_CHAT_ID, parse_mode="Markdown")

def get_boxscores_for_all_weeks(league: League):
    boxscores = {}
    curr_week = START_WEEK
    curr_boxscores = league.box_scores(curr_week)
    while(curr_boxscores[0].winner != 'UNDECIDED'):
        boxscores[curr_week] = []
        for boxscore in curr_boxscores:
            boxscores[curr_week].append({'team': boxscore.home_team.team_name, 'stats': boxscore.home_stats})
            boxscores[curr_week].append({'team': boxscore.away_team.team_name, 'stats': boxscore.away_stats})
        curr_week += 1
        curr_boxscores = league.box_scores(curr_week)
    return boxscores

def get_sorted_rankings(boxscores, calc_weeks=NUM_WEEKS_TO_CALC, week_offset=0):
    calc_weeks = calc_weeks+week_offset
    if len(boxscores) < (calc_weeks):
        logging.info(f"Cannot query for {calc_weeks} weeks, there aren't enough matchups yet")
        calc_weeks = len(boxscores)
        week_offset = 0
    
    team_ranking = {}
    if week_offset == 0:
        boxscore_splice = list(boxscores.values())[-calc_weeks:]
    else:
        boxscore_splice = list(boxscores.values())[-calc_weeks:-week_offset]
    for score_list in boxscore_splice:
        for cat in CATS:
            ordered_results = sorted(score_list, key=lambda item: item['stats'][cat]['value'])
            if cat == 'TO':
                ordered_results.reverse()
            logging.info(f"[{cat}]")
            for num, result in enumerate(ordered_results, start=1):
                team = result['team']
                logging.info(f"  {num}. {team}")
                if not team in team_ranking:
                    team_ranking[team] = 0
                team_ranking[team] += num
    sorted_rankings = sorted(team_ranking.items(), key=lambda item: item[1], reverse=True)
    return sorted_rankings

def print_ranking(current_rankings, last_rankings=[]):
    bot = telegram.Bot(token=BOT_API_KEY)
    woche_name = "Wochen"
    text = f"*Power Rankings*\n_{NUM_WEEKS_TO_CALC} {woche_name}_"
    print_to_channel(bot, text)
    for index, rank in enumerate(current_rankings, start=1):
        pos_diff = get_index_of_team(rank[0], last_rankings) - index
        text = f"*{index}.* ({pos_diff:+}) {rank[0]}: *{rank[1]} Power*"
        print_to_channel(bot, text)
        time.sleep(.5)

def get_index_of_team(team_name, ranking):
    for index, item in enumerate(ranking, start=1):
        if item[0] == team_name:
            return index
    return 0

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)

    # This gathers data from each matchup until the current one
    boxscores = get_boxscores_for_all_weeks(league)
    
    # This takes the results of the last weeks and calculates the rankings
    last_rankings = get_sorted_rankings(boxscores, week_offset=1)
    current_rankings = get_sorted_rankings(boxscores)

    # Post everything to telegram in the end
    print_ranking(current_rankings, last_rankings)

if __name__ == "__main__":
    main()