
import json
from datetime import date
from urllib2 import urlopen

from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class Parser(object):

    def __init__(self):
        super(Parser, self).__init__()

    def parse(self):
        raise NotImplementedError()


class KimonoParser(Parser):
    """

    """
    base = ''
    fields = ()
    url = ''

    def __init__(self, *args):
        super(KimonoParser, self).__init__()
        self.args = args
        if not self.url:
            raise ValueError('Value for url required.')

        self.soup = BeautifulSoup(urlopen(self.url.format(*args)).read())

    def parse(self):
        """
        Parse the data from the html page associated with the given URL.
        :return: All the records
        :rtype: list
        """
        rows = []
        types = {}

        if not self.base:
            raise MissingBaseError()

        # Scrape the fields out of the html
        for row in self.soup.select(self.base):
            next_row = {}
            for field, selector in self.fields:
                columns = row.select(selector)

                if len(columns) == 0:
                    # Handle missing field
                    next_type = types.get(field)
                    if not next_type:
                        # try to guess it
                        next_type = selector.split(' > ')[-1].split(':')[0]
                    if next_type:
                        if next_type == 'a':
                            next_row[field] = {
                                'text': '',
                                'href': ''
                            }
                        else:
                            next_row[field] = ''
                    continue
                elif len(columns) > 1:
                    raise RowMismatchError()

                # grab the first one
                column = columns[0]

                # Check to make sure it's the correct type
                if field in types:
                    if types[field] != column.name:
                        raise RowMismatchError()

                types[field] = column.name

                if column.name == 'a':
                    next_row[field] = {
                        'text': column.text,
                        'href': column.attrs.get('href')
                    }
                elif column.name == 'img':
                    next_row[field] = column.attrs.get('src')
                else:
                    next_row[field] = column.text

            rows.append(next_row)

        # Scan through a second time in case the fields were not discernable the first time through
        for row in rows:
            missing = False
            for field, selector in self.fields:
                if field not in row:
                    missing = True
                    if types[field] == 'a':
                        row[field] = {
                            'text': '',
                            'href': ''
                        }
                    else:
                        row[field] = ''
            if not missing:
                # All the fields were intact, so we're done
                break

        return self.post_process(rows)

    def post_process(self, data):
        """
        You may override this method to do any data post-processing.
        By default this will just return the original list.
        :param data: The list of data that was scraped
        :return: the transformed data
        :rtype: list
        """
        return data


class ConferencesParser(KimonoParser):
    url = 'http://espn.go.com/{0}-college-basketball/conferences'
    base = 'ul.medium-logos > li'
    fields = (
        ('name',        'div > h5 > a'),
        ('scoreboard',  'div.floatleft > br > span > a:nth-of-type(1)'),
        ('standings',   'div.floatleft > br > span > a:nth-of-type(2)'),
        ('stats',       'div.floatleft > br > span > a:nth-of-type(3)'),
        ('logo',        'div.floatleft > a > img'),
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
    base = 'div.span-4 > div.mod-container > div.mod-content > table > tr[class*=row]'
    fields = (
        ('team',            'td:nth-of-type(1) > a:nth-of-type(1)'),
        ('conf_record',     'td:nth-of-type(2)'),
        ('overall_record',  'td:nth-of-type(5)'),
        ('streak',          'td:nth-of-type(7)'),
        # ('ap_25',           'div:nth-of-type(30) > div > table > tr[class*=row] > '
        #                     'td:nth-of-type(2)'),
        # ('usa_today_25',    'div:nth-of-type(30) > div > table > tr[class*=row] > '
        #                     'td:nth-of-type(3)'),
        # ('home_record',     'div:nth-of-type(30) > div > table > tr[class*=row] > '
        #                     'td:nth-of-type(4)'),
        # ('away_record',     'div:nth-of-type(30) > div > table > tr[class*=row] > '
        #                     'td:nth-of-type(5)'),
    )

    def post_process(self, data):
        ret = []
        for team in data:
            conf_split = team['conf_record'].split('-')
            over_split = team['overall_record'].split('-')

            team['conf_wins'] = int(conf_split[0])
            team['conf_losses'] = int(conf_split[1])
            team['overall_wins'] = int(over_split[0])
            team['overall_losses'] = int(over_split[1])

            id_split = team['team']['href'].split('/')
            team['teamId'] = int(id_split[-2])

            total = team['conf_wins'] + team['conf_losses']

            team['conf_pct'] = float(team['conf_wins']) / total if total else 0

            ret.append(team)

        return ret


class GamesParser(Parser):
    url = 'http://scores.espn.go.com/{0}-college-basketball/scoreboard/_/group/50/date/{1}'

    def __init__(self, mens_womens, game_date=date.today().strftime("%Y%m%d")):
        super(GamesParser, self).__init__()
        # Make date param optional
        self.soup = BeautifulSoup(urlopen(self.url.format(mens_womens, game_date)).read())

    def parse(self):
        raw_scoreboard_data = None

        for script in self.soup.select('script'):
            if 'scoreboardData' in script.text:
                raw_scoreboard_data = script.text
                break

        if raw_scoreboard_data is None:
            raise RuntimeError('Could not find scoreboardData')

        open_brace = raw_scoreboard_data.find('{')
        close_brace = raw_scoreboard_data.find('};', open_brace)

        scoreboard_data = json.loads(raw_scoreboard_data[open_brace:close_brace+1])

        ret = []

        for event in scoreboard_data['events']:
            for competition in event['competitions']:
                game = {
                    'date': competition['date'],
                    'status': competition['status']['type']['detail'],
                    'attendance': competition['attendance'],
                    'conference_game': competition['conferenceCompetition'],
                    'neutral': competition['neutralSite'],
                }
                for competitor in competition['competitors']:
                    home_away = competitor['homeAway']
                    game['{0}_team'.format(home_away)] = competitor['team']
                    score = int(competitor['score']) if competitor['score'] else 0
                    game['{0}_score'.format(home_away)] = score
                    if 'records' in competitor:
                        for record in competitor['records']:
                            if record['type'] == 'total':
                                game['{0}_record'.format(home_away)] = record['summary']
                    else:
                        game['{0}_record'.format(home_away)] = '0-0'

                ret.append(game)

        return ret
