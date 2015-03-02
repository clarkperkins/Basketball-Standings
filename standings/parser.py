# An HTMLParser to parse basketball standings from ESPN

from HTMLParser import HTMLParser
from datetime import date

from bs4 import BeautifulSoup
import requests


class RowMismatchError(Exception):
    pass


class KimonoParser(object):
    """

    """
    fields = ()
    url = ''

    def __init__(self, *args):
        super(KimonoParser, self).__init__()
        self.args = args
        if not self.url:
            raise ValueError('Value for url required.')

        self.soup = BeautifulSoup(requests.get(self.url.format(*args)).text)
        self.rows = ()

    def parse(self):
        self.rows = []
        found = {}
        types = {}
        for field, selector in self.fields:
            found[field] = []
            for row in self.soup.select(selector):
                if field in types and types[field] != row.name:
                    raise RowMismatchError()

                types[field] = row.name

                if row.name == 'a':
                    found[field].append({
                        'text': row.text,
                        'href': row.attrs.get('href')
                    })
                elif row.name == 'img':
                    found[field].append(row.attrs.get('src'))
                else:
                    found[field].append(row.text)

        the_len = None
        for field, data in found.items():
            if the_len is not None and the_len != len(data):
                while len(data) < the_len:
                    if types[field] == 'a':
                        data.append({
                            'text': '',
                            'href': ''
                        })
                    else:
                        data.append('')

            the_len = len(data)

        idx = 0
        while True:
            next_row = {}
            for field, selector in self.fields:
                try:
                    next_row[field] = found[field][idx]
                except IndexError:
                    continue

            if not next_row:
                # If there was nothing added in the last iteration, stop
                break

            self.rows.append(next_row)
            idx += 1

        return self.post_process(self.rows)

    def post_process(self, data):
        """
        You may override this method to do any data post-processing
        :param data: The list of data that was scraped
        :return: the transformed data
        :rtype: list
        """
        return data


class ConferencesParser(KimonoParser):
    url = 'http://espn.go.com/{0}-college-basketball/conferences'
    fields = (
        ('name',        'ul > li > div > h5 > a'),
        ('scoreboard',  'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(1)'),
        ('standings',   'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(2)'),
        ('stats',       'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(3)'),
        ('logo',        'ul > li > div.floatleft > a > img'),
    )

    def post_process(self, data):
        for conf in data:
            conf['slug'] = conf['name']['text'].lower().replace(' ', '-')
            if self.args[0] == 'mens':
                conf['confId'] = int(conf['name']['href'].split('=')[1])
            elif self.args[0] == 'womens':
                conf['confId'] = int(conf['name']['href'].split('/')[-2])

        return data


class StandingsParser(KimonoParser):
    url = 'http://espn.go.com/{0}-college-basketball/conferences/standings/_/id/{1}'
    fields = (
        ('team',            'div:nth-of-type(28) > div > table > tr[class*=row] > '
                            'td:nth-of-type(1) > a:nth-of-type(1)'),
        ('conf_record',     'div:nth-of-type(28) > div > table > tr[class*=row] > '
                            'td:nth-of-type(2)'),
        ('overall_record',  'div:nth-of-type(28) > div > table > tr[class*=row] > '
                            'td:nth-of-type(5)'),
        ('streak',          'div:nth-of-type(28) > div > table > tr[class*=row] > '
                            'td:nth-of-type(7)'),
        ('ap_25',           'div:nth-of-type(30) > div > table > tr[class*=row] > '
                            'td:nth-of-type(2)'),
        ('usa_today_25',    'div:nth-of-type(30) > div > table > tr[class*=row] > '
                            'td:nth-of-type(3)'),
        ('home_record',     'div:nth-of-type(30) > div > table > tr[class*=row] > '
                            'td:nth-of-type(4)'),
        ('away_record',     'div:nth-of-type(30) > div > table > tr[class*=row] > '
                            'td:nth-of-type(5)'),
    )

    def post_process(self, data):
        for team in data:
            conf_split = team['conf_record'].split('-')
            over_split = team['overall_record'].split('-')

            team['conf_wins'] = int(conf_split[0])
            team['conf_losses'] = int(conf_split[1])
            team['overall_wins'] = int(over_split[0])
            team['overall_losses'] = int(over_split[1])

            id_split = team['team']['href'].split('/')
            team['teamId'] = int(id_split[-2])

            team['conf_pct'] = float(team['conf_wins']) / (team['conf_wins'] + team['conf_losses'])
        return data


class GamesParser(KimonoParser):
    url = 'http://scores.espn.go.com/ncb/scoreboard?confId=50&date={0}'
    fields = (
        ('away_team',   'div.team.visitor > div.team-capsule > p.team-name > span > a'),
        ('home_team',   'div.team.home > div.team-capsule > p.team-name > span > a'),
        ('status',      'div > div > div > div.game-status > p'),
        ('away_record', 'div > div > div.team.visitor > div.team-capsule > p.record'),
        ('home_record', 'div > div > div.team.home > div.team-capsule > p.record'),
        ('away_score',  'div > div > div.team.visitor > ul.score > li.final'),
        ('home_score',  'div > div > div.team.home > ul.score > li.final'),
        ('away_logo',   'div > div > div.team.visitor > div.logo-small > img'),
        ('home_logo',   'div > div > div.team.home > div.logo-small > img'),
        ('headline',    'div > div > div > div.recap-headline > a'),
    )

    def __init__(self, game_date=date.today().strftime("%Y%m%d")):
        # Make date param optional
        super(GamesParser, self).__init__(game_date)

    def post_process(self, data):
        for game in data:
            game['date'] = self.args[0]

            try:
                id_split = game['away_team']['href'].split('/')
                game['away_team']['teamId'] = int(id_split[-2])
            except IndexError:
                game['away_team']['teamId'] = 0

            try:
                id_split = game['home_team']['href'].split('/')
                game['home_team']['teamId'] = int(id_split[-2])
            except IndexError:
                game['home_team']['teamId'] = 0

        return data


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
    games_in_progress = []
    
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
        self.games_in_progress = []

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
                    new_data.append(" ".join(split2).replace("AM", "A&M"))
                #                print new_data
                self.results.append(new_data)
            #                print data
            #                print self.cur_class_data
            elif ':' in data:
                self.get_future_game = True
            self.get_team = False
        elif self.get_future_team:
            if ',' in data:
                self.games_in_progress.append(data.replace("AM", "A&M"))
                self.get_future_team = False
            else:
                self.future_game.append(data.replace("AM", "A&M"))
                self.get_future_team = False
                if len(self.future_game) is 2:
                    self.future_games.append(self.future_game)
                    self.future_game = []
