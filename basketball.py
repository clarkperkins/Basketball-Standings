#!/usr/bin/env python

import requests, json, sys
from datetime import date, timedelta
from BasketballParser import BasketballParser
from standings import order, record

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
