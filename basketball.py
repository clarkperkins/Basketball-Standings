#!/usr/bin/env python

import requests, json, sys
from datetime import date, timedelta
from HTMLParser import HTMLParser

class BasketballParser(HTMLParser):
    teams_in_conf = {}
    table_number = 0
    in_table = False
    get_team = False
    cur_class_data = ""
    results = []
    future_games = []
    get_future_game = False
    in_future_game_tag = False
    get_future_team = False
    future_game = []

    def __init__(self, teams):
        HTMLParser.__init__(self)
        self.teams_in_conf = teams
        self.table_number = 0
        self.in_table = False
        self.get_team = False
        self.results = []
        self.future_games = []
        self.get_future_game = False
        self.in_future_game_tag = False
        self.get_future_team = False
        self.future_game = []
    

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table_number is 0:
            self.table_number += 1
            self.in_table = True
#        elif self.in_table:
#            print tag, "with attrs", attrs
        elif self.in_table and tag == "tr":
            for attr in attrs[0]:
                if "team" in attr:
                    self.get_team = True
                    self.cur_class_data = attr
        elif self.get_future_game and tag == "td":
            self.in_future_game_tag = True
            self.get_future_game = False
        elif self.in_future_game_tag and tag == "a":
            self.get_future_team = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif self.in_future_game_tag and tag == "td":
            self.in_future_game_tag = False
    
    def handle_data(self, data):
        if self.get_team:
#            pass
            if ',' in data:
                class_data = self.cur_class_data.split(" ")
                id1 = int(class_data[1].split("-")[2])
                id2 = int(class_data[2].split("-")[2])
                if id1 not in self.teams_in_conf.keys() or id2 not in self.teams_in_conf.keys():
                    return
                split_data = data.split(", ")
                new_data = []
                for i in split_data:
                    split2 = i.split(" ")
                    if "OT" in split2[len(split2)-1]:
                        split2.pop()
                    if "#" in split2[0]:
                        del split2[0]
                    split2.pop()
                    new_data.append(" ".join(split2).replace("AM","A&M"))
#                print new_data
                self.results.append(new_data)
#                print data
#                print self.cur_class_data
            elif ':' in data:
                self.get_future_game = True
            self.get_team = False
        elif self.get_future_team:
            self.future_game.append(data.replace("AM", "A&M"))
            self.get_future_team = False
            if len(self.future_game) is 2:
                self.future_games.append(self.future_game)
                self.future_game = []

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


mens_womens = raw_input("Would you like standings for mens or womens basketball? ")

if mens_womens != "mens" and mens_womens != "womens":
    print "You must enter 'mens' or 'womens'.  Exiting."
    exit(1)

conf = raw_input("Enter your conference code now if you know it, otherwise press enter: ")

ESPN_URL = "http://api.espn.com/v1/sports/basketball/"+mens_womens+"-college-basketball"
API_KEY = "?apikey=ndzryyg4bp4zvjd43h7azdcp"


r = requests.get(ESPN_URL+API_KEY)

res = r.json()

conferences = {}
max_len = 0

for i in res['sports'][0]['leagues'][0]['groups'][0]['groups']:
    conferences[i['abbreviation']] = {'name':i['name'], 'id':i['groupId']}
    if len(i['name']) > max_len:
        max_len = len(i['name'])

if conf == "":
    print
    for i in conferences.keys():
        print conferences[i]['name'].ljust(max_len+1), i
    print
    conf = raw_input("Enter a conference: ")

if conf == "":
    print "\nYou must enter a conference.  Exiting."
    exit(1)

if conf not in conferences.keys():
    print "\nYou entered an invalid conference.  Exiting."
    exit(1)

id = conferences[conf]['id']


print "Fetching data",
sys.stdout.flush()

r = requests.get(ESPN_URL+"/teams"+API_KEY+"&groups="+str(id))

res = r.json()

errata = {
    'Mississippi St': 'Mississippi State',
    'NC State': 'North Carolina State'
}

teams_in_conf = {}
for i in res['sports'][0]['leagues'][0]['teams']:
    teams_in_conf[i['id']] = i['nickname']


stats = []
future_games = []

start_date = date(2013,11,8)
#start_date = date.today() - timedelta(1)

while start_date < date.today() + timedelta(10):
    print ".",
    sys.stdout.flush()
    SCHEDULE_URL = "http://espn.go.com/"+mens_womens+"-college-basketball/conferences/schedule/_/id/"+str(id)+"/date/"+start_date.strftime("%Y%m%d")+"/"+conf+"-conference"

    r = requests.get(SCHEDULE_URL)

    parser = BasketballParser(teams_in_conf)
    parser.feed(r.text.replace("A&M","AM"))

    stats.extend(parser.results)
    future_games.extend(parser.future_games)

    start_date += timedelta(6)

print

team_records = {}

for game in stats:
    if not team_records.has_key(game[0]):
        team_records[game[0]] = {'wins':[], 'losses':[]}
    if not team_records.has_key(game[1]):
        team_records[game[1]] = {'wins':[], 'losses':[]}
    team_records[game[0]]['wins'].append(game[1])
    team_records[game[1]]['losses'].append(game[0])

max_len = 0
for i in team_records.keys():
    if len(i) > max_len:
        max_len = len(i)

print

this_order = order(team_records, True)

print
print "Current Conference Standings:"

num = 1

for team in this_order:
    print repr(num).rjust(2), team.ljust(max_len+1), record(team_records, team)
    num += 1

print

possible_standings = {}

def compute_future_statistics(game_no):
    if game_no is len(future_games):
        team_records = {}
        for game in stats:
            if not team_records.has_key(game[0]):
                team_records[game[0]] = {'wins':[], 'losses':[]}
            if not team_records.has_key(game[1]):
                team_records[game[1]] = {'wins':[], 'losses':[]}
            team_records[game[0]]['wins'].append(game[1])
            team_records[game[1]]['losses'].append(game[0])

        this_order = order(team_records, False)

        for i in range(0, len(this_order)):
            if not possible_standings.has_key(this_order[i]):
                possible_standings[this_order[i]] = [0] * len(this_order)
            possible_standings[this_order[i]][i] += 1
    else:
        stats.append(future_games[game_no])
        compute_future_statistics(game_no + 1)
        stats.pop()
        stats.append([future_games[game_no][1], future_games[game_no][0]])
        compute_future_statistics(game_no + 1)
        stats.pop()

compute_future_statistics(0)

possible_percents = {}

num_possibilities = pow(2, len(future_games))

for team in possible_standings.keys():
    possible_percents[team] = []
    for num_games in possible_standings[team]:
        possible_percents[team].append(float(num_games)/num_possibilities*100)

print "Team:".ljust(max_len + 1),
for i in range(1, len(possible_percents.keys())+1):
    print repr(i).rjust(4)+" ",
print

for team in this_order:
    print team.ljust(max_len + 1),
    for percent in possible_percents[team]:
        if percent == 0.0:
            print "    -",
        else:
            print ("%.1f" % percent).rjust(5),
    print

print
