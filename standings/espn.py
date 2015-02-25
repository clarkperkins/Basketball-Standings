# Functions for getting data from ESPN

import sys
from datetime import timedelta

import requests

from standings.parser import BasketballParser


class EndpointNotFound(Exception):
    pass


class InvalidSport(Exception):
    pass


class ESPN(object):
    """

    """

    ESPN_API_URL = 'http://api.espn.com/v1/sports{0}/?apikey={1}'
    EXCLUDE = ('cricket', 'soccer', 'mma', 'racing', 'golf', 'water-polo', 'lacrosse', 'softball',
               'tennis', 'volleyball', 'hockey')

    def __init__(self, api_key):
        self.api_key = api_key
        self._sports = {}
        self._leagues = {}

    def get_url(self, endpoint, **kwargs):
        """
        Get the full endpoint URL for the given endpoint

        :param endpoint: the api endpoint
        :return: the formatted url
        :rtype: str
        """
        assert isinstance(endpoint, str)
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        if endpoint.endswith('/'):
            endpoint = endpoint[:-2]

        get_params = ['{0}={1}'.format(k, v) for k, v in kwargs.items()]

        ret = self.ESPN_API_URL.format(endpoint, self.api_key)

        if get_params:
            ret = '{0}&{1}'.format(ret, '&'.join(get_params))

        return ret

    def get_sports(self, force=False):
        """
        Get a list of all the available sports

        :return: the list of sports
        :rtype: dict
        """
        if self._sports and not force:
            return self._sports

        r = requests.get('http://espn.go.com/sports/')

        soup = BeautifulSoup(r.text)

        # grab the div we want
        sports_div = soup.find_all('div', 'span-4 bg-opaque')[0].contents
        sports_div.remove('\n')

        for section in sports_div:
            section.contents.remove('\n')
            for row in section.contents:
                row.contents.remove('\n')
                for col in row:
                    print col.find_all('h4')
                    print

        sports = r.json()['sports']

        for sport in sports:
            leagues = {}

            for league in sport.get('leagues', []):
                leagues[league['abbreviation']] = {
                    'name': league['name'],
                    'sport': sport['name'],
                }
                self._leagues[league['abbreviation']] = leagues[league['abbreviation']]

            self._sports[sport['name']] = leagues

        return self._sports

    def get_conferences(self, league, force_reload=False):
        """
        Get a list of conferences

        :param sport: the sport to get conferences for
        :return: the list of conferences
        :rtype: list
        """
        if sport not in self.get_sports(force_reload):
            raise InvalidConference()

        r = requests.get(self.get_url('/{0}/{1}'.format(self.get_sports()[sport]['sport'], sport)))

        conferences = r.json()['sports'][0]['leagues'][0]['groups']

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


def get_games_list(mens_womens, conf, conference_id, start_date, tourney_date, teams_in_conf):
    print "Fetching data",
    sys.stdout.flush()

    # r = requests.get(ESPN_API_URL.format(mens_womens) + "/teams" + API_KEY
    #                  + "&groups=" + str(conference_id))
    #
    # res = r.json()
    #
    # teams_in_conf = {}
    # for i in res['sports'][0]['leagues'][0]['teams']:
    #     teams_in_conf[i['id']] = i['nickname']

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
