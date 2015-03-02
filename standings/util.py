# Utility functions for calculating the rankings of basketball teams
import sys
from .db import Session
from .models import Team


class Utils(object):

    def __init__(self):
        self.total_possibilities = None
        self.hell = None
        self.stats = None
        self.future_games = None
        self.possible_standings = None

        self.session = None

    def get_win_loss_matrix(self, games):
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

    def order(self, team_recs, print_ties):
        the_order = team_recs.keys()
        percents = {}
        for team in the_order:
            wins = len(team_recs[team]['wins'])
            games = wins + len(team_recs[team]['losses'])
            percent = float(wins) / games

            if percent not in percents:
                percents[percent] = []
            percents[percent].append(team)
        index = 0
        for i in sorted(percents.keys(), reverse=True):
            if len(percents[i]) is 1:
                the_order[index] = percents[i][0]
                index += 1
            else:
                orig_index = index
                for team in percents[i]:
                    the_order[index] = team
                    index += 1
                self.break_ties(team_recs, the_order, orig_index, index-1, print_ties)
        return the_order

    def check_record(self, team_recs, team, other_teams, print_ties):
        self.session = Session()
        wins = 0
        losses = 0
        for i in team_recs[team]['wins']:
            if i in other_teams:
                wins += 1
        for i in team_recs[team]['losses']:
            if i in other_teams:
                losses += 1
        if print_ties:
            print self.session.query(Team).get(team).name, "is", str(wins)+"-"+str(losses), "vs",
            for i in other_teams:
                print self.session.query(Team).get(i).name+" ",
            print
        return [wins, losses]

    def break_ties(self, team_recs, the_order, lo, hi, print_ties):
        if hi - lo is 1:
            rec = self.check_record(team_recs, the_order[lo], [the_order[hi]], print_ties)
            if rec[1] > rec[0]:
                the_order[lo], the_order[hi] = the_order[hi], the_order[lo]
            elif rec[1] is rec[0]:
                for index in range(0, len(the_order)):
                    if index not in range(lo, hi+1):
                        rec1 = self.check_record(team_recs, the_order[lo], [the_order[index]], print_ties)
                        rec2 = self.check_record(team_recs, the_order[hi], [the_order[index]], print_ties)
                        rec1_pct = 0.0
                        rec2_pct = 0.0
                        if rec1[0] + rec1[1] is not 0:
                            rec1_pct = float(rec1[0]) / (rec1[0] + rec1[1])
                        if rec2[0] + rec2[1] is not 0:
                            rec2_pct = float(rec2[0]) / (rec2[0] + rec2[1])
                        if rec2_pct > rec1_pct or (rec1[0] is 0 and rec2[0] is not 0):
                            the_order[lo], the_order[hi] = the_order[hi], the_order[lo]
                            break
                        elif rec1_pct < rec2_pct or (rec2[0] is 0 and rec1[0] is not 0):
                            break
        else:
            percents = {}
            for index in range(lo, hi+1):
                rec = self.check_record(team_recs, the_order[index], the_order[lo:hi+1], print_ties)
                percent = 0
                if rec[0] + rec[1] is not 0:
                    percent = float(rec[0]) / (rec[0] + rec[1])
                if percent not in percents.keys():
                    percents[percent] = []
                percents[percent].append(the_order[index])
            index = lo
            for pct in sorted(percents.keys(), reverse=True):
                if len(percents[pct]) is 1:
                    the_order[index] = percents[pct][0]
                    index += 1
                elif len(percents[pct]) is 2:
                    orig_index = index
                    for team in percents[pct]:
                        the_order[index] = team
                        index += 1
                    self.break_ties(team_recs, the_order, orig_index, index-1, print_ties)
                else:
                    should_break = False
                    for idx in range(0, len(the_order)):
                        if idx not in range(index, index+len(percents[pct])+1):
                            sub_pcts = {}
                            for team in percents[pct]:
                                sub = self.check_record(team_recs, team, [the_order[idx]], print_ties)
                                if float(sub[0])/(sub[0]+sub[1]) not in sub_pcts:
                                    sub_pcts[float(sub[0])/(sub[0]+sub[1])] = []
                                sub_pcts[float(sub[0])/(sub[0]+sub[1])].append(team)
    #                        print sub_pcts
                            for sub_pct in sorted(sub_pcts.keys(), reverse=True):
                                if len(sub_pcts[sub_pct]) is 1:
                                    the_order[index] = sub_pcts[sub_pct][0]
                                    index += 1
                                    should_break = True
                                elif len(sub_pcts[sub_pct]) < len(percents[pct]):
                                    orig_index = index
                                    for team in sub_pcts[sub_pct]:
                                        the_order[index] = team
                                        index += 1
                                    self.break_ties(team_recs, the_order, orig_index, index-1, print_ties)
                                    should_break = True

                            if should_break:
                                break

    def record(self, team_records, team):
        return str(len(team_records[team]['wins']))+"-"+str(len(team_records[team]['losses']))

    def get_future_statistics(self, past_games, fut_games):
        self.total_possibilities = pow(2, len(fut_games))
        self.hell = 0
        self.stats = past_games
        self.future_games = fut_games
        self.possible_standings = {}

        print

        self.prev_print = '0'
        sys.stdout.write(self.prev_print)

        def compute_future_statistics(game_no):
            sys.stdout.write('\b'*len(self.prev_print))
            self.prev_print = str(round(float(self.hell) / self.total_possibilities * 100, 2)) + '%'
            sys.stdout.write(self.prev_print)
            sys.stdout.flush()
            if game_no == len(self.future_games):
                team_records = self.get_win_loss_matrix(self.stats)

                this_order = self.order(team_records, False)

                for i in range(0, len(this_order)):
                    if this_order[i] not in self.possible_standings:
                        self.possible_standings[this_order[i]] = [0] * len(this_order)
                    self.possible_standings[this_order[i]][i] += 1

                self.hell += 1
            else:
                self.stats.append(self.future_games[game_no])
                compute_future_statistics(game_no + 1)
                self.stats.pop()
                self.stats.append((self.future_games[game_no][1], self.future_games[game_no][0]))
                compute_future_statistics(game_no + 1)
                self.stats.pop()

        compute_future_statistics(0)

        return self.possible_standings
