# Functions for getting data from ESPN

import sys
from datetime import timedelta

import requests

from standings.parser import BasketballParser


API_KEY = "?apikey=ndzryyg4bp4zvjd43h7azdcp"

ESPN_API_URL = "http://api.espn.com/v1/sports/basketball/{0}-college-basketball"


def get_conference_list(mens_womens):
    r = requests.get(ESPN_API_URL.format(mens_womens)+API_KEY)

    res = r.json()

    conferences = {}
    max_len = 0

    for i in res['sports'][0]['leagues'][0]['groups'][0]['groups']:
        conferences[i['abbreviation']] = {'name': i['name'], 'id': i['groupId']}
        if len(i['name']) > max_len:
            max_len = len(i['name'])

    conferences['max_len'] = max_len

    return conferences


def get_games_list(mens_womens, conf, conference_id, start_date, tourney_date):
    print "Fetching data",
    sys.stdout.flush()

    r = requests.get(ESPN_API_URL.format(mens_womens) + "/teams" + API_KEY
                     + "&groups=" + str(conference_id))

    res = r.json()

    teams_in_conf = {}
    for i in res['sports'][0]['leagues'][0]['teams']:
        teams_in_conf[i['id']] = i['nickname']

    stats = []
    future_games = []
    games_in_progress = []

    end_date = tourney_date-timedelta(6)

    while start_date < end_date:
        print ".",
        sys.stdout.flush()
        schedule_url = "http://espn.go.com/" + mens_womens \
            + "-college-basketball/conferences/schedule/_/id/" + str(conference_id) + "/date/" \
            + end_date.strftime("%Y%m%d") + "/" + conf + "-conference"
        
        r = requests.get(schedule_url)
        
        if r.status_code is not 200:
            print "request for", str(end_date), "failed."
        
        parser = BasketballParser(teams_in_conf)
        parser.feed(r.text.replace("A&M", "AM"))
        
        stats.extend(parser.results)
        future_games.extend(parser.future_games)
        games_in_progress.extend(parser.games_in_progress)
        
        end_date -= timedelta(6)

    return {
        'past_games': stats,
        'future_games': future_games,
        'games_in_progress': games_in_progress
    }
