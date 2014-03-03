# Functions for getting data from ESPN

import requests, json, sys
from BasketballParser import BasketballParser
from datetime import date, timedelta

API_KEY = "?apikey=ndzryyg4bp4zvjd43h7azdcp"

def get_conference_list(mens_womens):
    ESPN_API_URL = "http://api.espn.com/v1/sports/basketball/"+mens_womens+"-college-basketball"

    r = requests.get(ESPN_API_URL+API_KEY)

    res = r.json()

    conferences = {}
    max_len = 0

    for i in res['sports'][0]['leagues'][0]['groups'][0]['groups']:
        conferences[i['abbreviation']] = {'name':i['name'], 'id':i['groupId']}
        if len(i['name']) > max_len:
            max_len = len(i['name'])

    conferences['max_len'] = max_len

    return conferences



def get_games_list(mens_womens, conf, id, start_date, end_date):
    ESPN_API_URL = "http://api.espn.com/v1/sports/basketball/"+mens_womens+"-college-basketball"

    print "Fetching data",
    sys.stdout.flush()

    r = requests.get(ESPN_API_URL+"/teams"+API_KEY+"&groups="+str(id))

    res = r.json()

    teams_in_conf = {}
    for i in res['sports'][0]['leagues'][0]['teams']:
        teams_in_conf[i['id']] = i['nickname']


    stats = []
    future_games = []

    while start_date < end_date:
        print ".",
        sys.stdout.flush()
        SCHEDULE_URL = "http://espn.go.com/"+mens_womens+"-college-basketball/conferences/schedule/_/id/"+str(id)+"/date/"+start_date.strftime("%Y%m%d")+"/"+conf+"-conference"
        
        r = requests.get(SCHEDULE_URL)
        
        parser = BasketballParser(teams_in_conf)
        parser.feed(r.text.replace("A&M","AM"))
        
        stats.extend(parser.results)
        future_games.extend(parser.future_games)
        
        start_date += timedelta(6)

    return {'past_games':stats, 'future_games':future_games}

