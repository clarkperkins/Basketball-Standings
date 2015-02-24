# An HTMLParser to parse basketball standings from ESPN

from HTMLParser import HTMLParser
import json

from bs4 import BeautifulSoup
import requests


class KimonoParser(object):
    """

    """
    fields = ()
    url = ''

    def __init__(self, *args):
        super(KimonoParser, self).__init__()
        if not self.url:
            raise ValueError('Value for url required.')

        self.soup = BeautifulSoup(requests.get(self.url.format(*args)).text)
        self.rows = ()

    def parse(self):
        self.rows = []
        found = {}
        for field, selector in self.fields:
            found[field] = []
            for row in self.soup.select(selector):
                if row.name == 'a':
                    found[field].append({
                        'text': row.text,
                        'href': row.attrs.get('href')
                    })
                elif row.name == 'img':
                    found[field].append(row.attrs.get('src'))
                else:
                    found[field].append(json.loads(row.text))

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

        return self.rows


class ConferencesParser(KimonoParser):
    url = 'http://espn.go.com/mens-college-basketball/conferences'
    fields = (
        ('name', 'ul > li > div > h5 > a'),
        ('scoreboard', 'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(1)'),
        ('standings', 'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(2)'),
        ('stats', 'ul.medium-logos > li > div.floatleft > br > span > a:nth-of-type(3)'),
        ('logo', 'ul > li > div.floatleft > a > img'),
    )


class StandingsParser(KimonoParser):
    url = 'http://espn.go.com/mens-college-basketball/conferences/standings/_/id/{0}'
    fields = (
        ('team', 'div:nth-of-type(28) > div > table > tr[class*=row] > td:nth-of-type(1) > a:nth-of-type(1)'),
        ('conf_record', 'div:nth-of-type(28) > div > table > tr[class*=row] > td:nth-of-type(2)'),
        ('overall_record', 'div:nth-of-type(28) > div > table > tr[class*=row] > td:nth-of-type(5)'),
        ('streak', 'div:nth-of-type(28) > div > table > tr[class*=row] > td:nth-of-type(7)'),
        ('ap_25', 'div:nth-of-type(30) > div > table > tr[class*=row] > td:nth-of-type(2)'),
        ('usa_today_25', 'div:nth-of-type(30) > div > table > tr[class*=row] > td:nth-of-type(3)'),
        ('home_record', 'div:nth-of-type(30) > div > table > tr[class*=row] > td:nth-of-type(4)'),
        ('away_record', 'div:nth-of-type(30) > div > table > tr[class*=row] > td:nth-of-type(5)'),
    )


class GamesParser(KimonoParser):
    url = 'http://scores.espn.go.com/ncb/scoreboard?confId=50'
    fields = (
        ('away_team', 'div.team.visitor > div.team-capsule > p.team-name > span > a'),
        ('home_team', 'div.team.home > div.team-capsule > p.team-name > span > a'),
        ('status', 'div > div > div > div.game-status > p'),
        ('away_record', 'div > div > div.team.visitor > div.team-capsule > p.record'),
        ('home_record', 'div > div > div.team.home > div.team-capsule > p.record'),
        ('away_score', 'div > div > div.team.visitor > ul.score > li.final'),
        ('home_score', 'div > div > div.team.home > ul.score > li.final'),
        ('away_logo', 'div > div > div.team.visitor > div.logo-small > img'),
        ('home_logo', 'div > div > div.team.home > div.logo-small > img'),
        ('headline', 'div > div > div > div.recap-headline > a'),
    )


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
