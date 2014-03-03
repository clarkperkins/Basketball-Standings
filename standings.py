# Utility functions for calculating the rankings of basketball teams


def order(team_recs, print_ties):
    the_order = team_recs.keys()
    percents = {}
    for team in the_order:
        percent = float(len(team_recs[team]['wins']))/(len(team_recs[team]['wins'])+len(team_recs[team]['losses']))
        if not percents.has_key(percent):
            percents[percent] = []
        percents[percent].append(team)
    index = 0
    for i in sorted(percents.keys(),reverse=True):
        if len(percents[i]) is 1:
            the_order[index] = percents[i][0]
            index += 1
        else:
            orig_index = index
            for team in percents[i]:
                the_order[index] = team
                index += 1
            break_ties(team_recs, the_order, orig_index, index-1, print_ties)
    return the_order


def check_record(team_recs, team, other_teams, print_ties):
    wins = 0
    losses = 0
    for i in team_recs[team]['wins']:
        if i in other_teams:
            wins += 1
    for i in team_recs[team]['losses']:
        if i in other_teams:
            losses += 1
    if print_ties:
        print team, "is", str(wins)+"-"+str(losses), "vs",
        for i in other_teams:
            print i+" ",
        print
    return [wins, losses]

def break_ties(team_recs, the_order, lo, hi, print_ties):
    if hi - lo is 1:
        rec = check_record(team_recs, the_order[lo], [the_order[hi]], print_ties)
        if rec[1] > rec[0]:
            the_order[lo], the_order[hi] = the_order[hi], the_order[lo]
        elif rec[1] is rec[0]:
            for index in range(0, len(the_order)):
                if index not in range(lo, hi+1):
                    rec1 = check_record(team_recs, the_order[lo], [the_order[index]], print_ties)
                    rec2 = check_record(team_recs, the_order[hi], [the_order[index]], print_ties)
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
            rec = check_record(team_recs, the_order[index], the_order[lo:hi+1], print_ties)
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
                break_ties(team_recs, the_order, orig_index, index-1, print_ties)

def record(team_records, team):
    return str(len(team_records[team]['wins']))+"-"+str(len(team_records[team]['losses']))


