from espn_api.basketball import League #Ref: https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball
from tabulate import tabulate
import os
import sys

if not 'ESPN_S2' in os.environ:
    print("You need to set the right env vars. Check README.md")
    sys.exit(1)

ESPN_S2 = os.environ['ESPN_S2']
SWID = os.environ['SWID']
LEAGUE_ID = int(os.environ['LEAGUE_ID'])
LEAGUE_YEAR = int(os.environ['LEAGUE_YEAR'])

ONLY_CALC_LAST_X_WEEK = 4

def main():
    league = League(league_id=LEAGUE_ID, year=LEAGUE_YEAR, espn_s2=ESPN_S2, swid=SWID)

    team_results = {}
    curr_week = 1
    curr_scoreboard = league.scoreboard(curr_week)
    while(curr_scoreboard[0].winner != 'UNDECIDED'):
        team_results[curr_week] = []
        for match in curr_scoreboard:
            team_results[curr_week].append({'team': match.home_team.team_name, 'score': match.home_final_score})
            team_results[curr_week].append({'team': match.away_team.team_name, 'score': match.away_final_score})
        curr_week += 1
        curr_scoreboard = league.scoreboard(curr_week)

    team_ranking = {}
    for result in list(team_results.values())[-ONLY_CALC_LAST_X_WEEK:]:
        ordered_results = sorted(result, key=lambda d: d['score'])
        for num, result in enumerate(ordered_results, start=1):
            team = result['team']
            if not team in team_ranking:
                team_ranking[team] = 0
            team_ranking[team] += num

    sorted_rankings = sorted(team_ranking.items(), key=lambda item: item[1], reverse=True)
    headers = ["Place", "Team", "Points"]
    tab = []
    for index, rank in enumerate(sorted_rankings, start=1):
        tab.append([f"{index}.", rank[0], rank[1]])
    
    print(tabulate(tab, headers=headers))
            

if __name__ == "__main__":
    main()