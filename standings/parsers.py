from datetime import date
from urllib2 import urlopen

from bs4 import BeautifulSoup


class RowMismatchError(Exception):
    pass


class MissingBaseError(Exception):
    pass


class KimonoParser(object):
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
        saved = None

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
    base = 'div:nth-of-type(28) > div > table > tr[class*=row]'
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
    base = 'div.gameDay-Container div.mod-content'
    fields = (
        ('away_team',   'div.team.visitor > div.team-capsule > p.team-name > span > a'),
        ('home_team',   'div.team.home > div.team-capsule > p.team-name > span > a'),
        ('status',      'div.game-status > p'),
        ('away_record', 'div.team.visitor > div.team-capsule > p.record'),
        ('home_record', 'div.team.home > div.team-capsule > p.record'),
        ('away_score',  'div.team.visitor > ul.score > li.final'),
        ('home_score',  'div.team.home > ul.score > li.final'),
        ('away_logo',   'div.team.visitor > div.logo-small > img'),
        ('home_logo',   'div.team.home > div.logo-small > img'),
        ('headline',    'div.recap-headline > a'),
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

            # if 'headline' not in game:
            #     import json
            #     print json.dumps(game, indent=3)

        return data
