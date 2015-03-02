# Functions for getting data from ESPN

import sys
from datetime import timedelta

import requests

from .parsers import BasketballParser


def get_games_list(mens_womens, conf, conference_id, start_date, tourney_date, teams_in_conf):
    print "Fetching data",
    sys.stdout.flush()

    stats = []
    future_games = []
    games_in_progress = []

    end_date = tourney_date - timedelta(6)

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
