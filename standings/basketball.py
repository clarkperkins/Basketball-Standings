#!/usr/bin/env python

from datetime import date

from standings.standings import order, record, get_win_loss_matrix, get_future_statistics
from standings import espn


mens_womens = raw_input("Would you like standings for mens or womens basketball? ")

if mens_womens != "mens" and mens_womens != "womens":
    print "You must enter 'mens' or 'womens'.  Exiting."
    exit(1)

conf = raw_input("Enter your conference code now if you know it, otherwise press enter: ")


conferences = espn.get_conference_list(mens_womens)

max_len = conferences['max_len']

del conferences['max_len']

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

year = raw_input("What year? (press enter for current year) ")

if year == "":
    year = date.today().year
else:
    year = int(year)

tourney_month = int(raw_input("Month of conference tourney start date: "))

if tourney_month > 12:
    print "You entered an invalid month. Exiting."
    exit(1)

tourney_day = int(raw_input("Day of conference tourney start date: "))

if tourney_day > 31:
    print "You entered an invalid day. Exiting."
    exit(1)

conference_id = conferences[conf]['id']


games_list = espn.get_games_list(mens_womens,
                                 conf,
                                 conference_id,
                                 date(year-1, 11, 1),
                                 date(year, tourney_month, tourney_day))

past_games = games_list['past_games']
future_games = games_list['future_games']
games_in_progress = games_list['games_in_progress']

print

team_records = get_win_loss_matrix(past_games)


max_len = 0
num_games = 0
for i in team_records.keys():
    if len(i) > max_len:
        max_len = len(i)
    num_games += len(team_records[i]['wins'])
    num_games += len(team_records[i]['losses'])

avg_num_games = int(float(num_games) / len(team_records.keys()))


for team in team_records.keys():
    if team in team_records:
        num_games_team = len(team_records[team]['wins']) + len(team_records[team]['losses'])
        if avg_num_games - num_games_team > 5:
            del team_records[team]
            for i in team_records.keys():
                for j in range(0, len(team_records[i]['wins'])):
                    if j < len(team_records[i]['wins']):
                        if team_records[i]['wins'][j] == team:
                            del team_records[i]['wins'][j]
                for j in range(0, len(team_records[i]['losses'])):
                    if j < len(team_records[i]['losses']):
                        if team_records[i]['losses'][j] == team:
                            del team_records[i]['losses'][j]

print

this_order = order(team_records, True)

print
print "Current Conference Standings:"

num = 1

for team in this_order:
    print repr(num).rjust(2), team.ljust(max_len+1), record(team_records, team)
    num += 1

print
print

print "There are", len(games_in_progress), "games in progress."
for game in games_in_progress:
    print game

print
print "There are", len(future_games), "games left."

if 0 < len(future_games) < 20:
    for game in future_games:
        print game[0], "@", game[1]
    
    possible_standings = get_future_statistics(past_games, future_games)

    possible_percents = {}

    num_possibilities = pow(2, len(future_games))

    for team in possible_standings.keys():
        possible_percents[team] = []
        for num_games in possible_standings[team]:
            possible_percents[team].append(float(num_games)/num_possibilities*100)

    print
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
