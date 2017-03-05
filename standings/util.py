# Utility functions for calculating the rankings of basketball teams
import sys
from .db import Session
from .models import Team

prev_print = None
current_iteration = None


def get_win_loss_matrix(games):
    team_records = {}

    for game in games:
        if type(game) == tuple:
            winner = game[0]
            loser = game[1]
        else:

            if game.home_score > game.away_score:
                winner = game.home_team_id
                loser = game.away_team_id
            else:
                winner = game.away_team_id
                loser = game.home_team_id
        team_records.setdefault(winner, {'wins': [], 'losses': []})['wins'].append(loser)
        team_records.setdefault(loser, {'wins': [], 'losses': []})['losses'].append(winner)

    return team_records


def order(team_recs, print_ties):
    the_order = team_recs.keys()
    percents = {}
    for team in the_order:
        wins = len(team_recs[team]['wins'])
        games = wins + len(team_recs[team]['losses'])
        percent = float(wins) / games
        percents.setdefault(percent, []).append(team)
    index = 0
    for percent, teams in sorted(percents.items(), key=lambda x: x[0], reverse=True):
        if len(teams) == 1:
            the_order[index] = teams[0]
            index += 1
        else:
            orig_index = index
            for team in teams:
                the_order[index] = team
                index += 1
            break_ties(team_recs, the_order, orig_index, index - 1, print_ties)

    return the_order


def check_record(team_recs, team, other_teams, print_ties):
    session = Session()
    wins = 0
    losses = 0
    for i in team_recs[team]['wins']:
        if i in other_teams:
            wins += 1
    for i in team_recs[team]['losses']:
        if i in other_teams:
            losses += 1
    if print_ties:
        other_team_names = [session.query(Team).get(x).name for x in other_teams]
        print('{0} is {1}-{2} vs {3}'.format(session.query(Team).get(team).name,
                                             wins, losses, '  '.join(other_team_names)))
    return wins, losses


def break_ties(team_recs, the_order, lo, hi, print_ties):
    if hi - lo == 1:
        rec = check_record(team_recs, the_order[lo], [the_order[hi]], print_ties)
        if rec[1] > rec[0]:
            the_order[lo], the_order[hi] = the_order[hi], the_order[lo]
        elif rec[1] == rec[0]:
            for index, team_id in enumerate(the_order):
                if index not in range(lo, hi + 1):
                    rec1 = check_record(team_recs, the_order[lo], [team_id], print_ties)
                    rec2 = check_record(team_recs, the_order[hi], [team_id], print_ties)
                    rec1_pct = 0.0
                    rec2_pct = 0.0
                    if rec1[0] + rec1[1] != 0:
                        rec1_pct = float(rec1[0]) / (rec1[0] + rec1[1])
                    if rec2[0] + rec2[1] != 0:
                        rec2_pct = float(rec2[0]) / (rec2[0] + rec2[1])
                    if rec2_pct > rec1_pct:
                        # Swap them
                        the_order[lo], the_order[hi] = the_order[hi], the_order[lo]
                        break
                    elif rec1_pct < rec2_pct:
                        # Leave them alone, and stop
                        break
    else:
        percents = {}
        for index in range(lo, hi+1):
            rec = check_record(team_recs, the_order[index], the_order[lo:hi+1], print_ties)
            percent = 0
            if rec[0] + rec[1] != 0:
                percent = float(rec[0]) / (rec[0] + rec[1])
            if percent not in percents.keys():
                percents[percent] = []
            percents[percent].append(the_order[index])
        index = lo
        for pct, teams in sorted(percents.items(), key=lambda x: x[0], reverse=True):
            if len(teams) == 1:
                the_order[index] = teams[0]
                index += 1
            elif len(teams) == 2:
                orig_index = index
                for team in teams:
                    the_order[index] = team
                    index += 1
                break_ties(team_recs, the_order, orig_index, index-1, print_ties)
            else:
                should_break = False
                for idx in range(0, len(the_order)):
                    if idx not in range(index, index + len(percents[pct]) + 1):
                        sub_pcts = {}
                        for team in percents[pct]:
                            sub = check_record(team_recs, team, [the_order[idx]], print_ties)
                            if sub[0] == 0 and sub[1] == 0:
                                if 0 not in sub_pcts:
                                    sub_pcts[0] = []
                                sub_pcts[0].append(team)
                            else:
                                if float(sub[0]) / (sub[0] + sub[1]) not in sub_pcts:
                                    sub_pcts[float(sub[0])/(sub[0]+sub[1])] = []
                                sub_pcts[float(sub[0])/(sub[0]+sub[1])].append(team)
                        # print sub_pcts
                        for sub_pct in sorted(sub_pcts.keys(), reverse=True):
                            if len(sub_pcts[sub_pct]) == 1:
                                the_order[index] = sub_pcts[sub_pct][0]
                                index += 1
                                should_break = True
                            elif len(sub_pcts[sub_pct]) < len(percents[pct]):
                                orig_index = index
                                for team in sub_pcts[sub_pct]:
                                    the_order[index] = team
                                    index += 1
                                break_ties(team_recs, the_order, orig_index, index-1, print_ties)
                                should_break = True

                        if should_break:
                            break


def record(team_records, team):
    return str(len(team_records[team]['wins']))+"-"+str(len(team_records[team]['losses']))


def get_future_statistics(past_games, future_games):
    global prev_print
    global current_iteration

    total_possibilities = pow(2, len(future_games))
    current_iteration = 0
    possible_standings = {}
    prev_print = '0'

    print('')

    sys.stdout.write(prev_print)

    def compute_future_statistics(game_no):
        global current_iteration
        global prev_print
        sys.stdout.write('\b' * len(prev_print))
        prev_print = str(round(float(current_iteration) / total_possibilities * 100, 2)) + '%'
        sys.stdout.write(prev_print)
        sys.stdout.flush()
        if game_no == len(future_games):
            team_records = get_win_loss_matrix(past_games)

            this_order = order(team_records, False)

            for i, team_id in enumerate(this_order):
                if team_id not in possible_standings:
                    possible_standings[team_id] = [0] * len(this_order)
                possible_standings[team_id][i] += 1

            current_iteration += 1
        else:
            past_games.append(future_games[game_no])
            compute_future_statistics(game_no + 1)
            past_games.pop()
            past_games.append((future_games[game_no][1], future_games[game_no][0]))
            compute_future_statistics(game_no + 1)
            past_games.pop()

    compute_future_statistics(0)

    return possible_standings
