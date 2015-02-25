
from .util import order, record, get_win_loss_matrix, get_future_statistics

from datetime import date

from tabulate import tabulate

from .parser import StandingsParser, ConferencesParser, GamesParser
from . import espn


class BasketballStandings(object):
    """

    """
    def __init__(self, mens_womens, conference):
        super(BasketballStandings, self).__init__()

        self.mens_womens = mens_womens
        self.conference = conference
        self.conf_id = None
        self.standings_dict = None
        self.team_ids = None
        self.future_games = None

        self.conferences_parser = ConferencesParser(self.mens_womens)
        self.games_parser = GamesParser()
        self.standings_parser = None

    def validate_input(self):
        while self.mens_womens not in ('mens', 'womens'):
            self.mens_womens = raw_input('Would you like standings for mens or womens basketball? ')

        conferences = self.conferences_parser.parse()

        # if not self.conference:
        #     self.conference = raw_input('Enter your conference code now if you know it, otherwise '
        #                                 'press enter: ')

        if not self.conference:
            print 'Conference choices: '
            for conf in conferences:
                print '   ', conf['slug']

            exit(1)
            # self.conference = raw_input("Enter a conference: ")

        if self.conference not in map(lambda x: x['slug'], conferences):
            print 'Invalid conference:', self.conference
            exit(1)

        for conf in conferences:
            if conf['slug'] == self.conference:
                self.conf_id = conf['confId']
                break

    def get_standings(self):
        self.standings_parser = StandingsParser(self.mens_womens, self.conf_id)

        standings = self.standings_parser.parse()

        self.standings_dict = {}

        for team in standings:
            self.standings_dict[team['teamId']] = team

        self.team_ids = map(lambda x: x['teamId'], standings)

    def get_todays_games(self):
        todays_games = self.games_parser.parse()

        self.future_games = []

        for game in todays_games:
            if 'Final' not in game['status']:
                if game['home_team']['teamId'] in self.team_ids and \
                        game['away_team']['teamId'] in self.team_ids:
                    # We found an in-conference game
                    self.future_games.append((
                        game['home_team']['teamId'],
                        game['away_team']['teamId']
                    ))

    def get_future_games(self):
        pass

    def _make_row(self, item):
        return item[1]['team']['text'], item[1]['conf_record'], item[1]['overall_record']

    def print_records(self):
        tabular = map(self._make_row, sorted(self.standings_dict.items(),
                                             reverse=True,
                                             key=lambda x: x[1]['conf_pct']))
        print tabulate(tabular)

    def run(self):
        self.validate_input()
        self.get_standings()
        # self.get_todays_games()

        conf_teams = {}
        for id, team in self.standings_dict.items():
            conf_teams[id] = team['team']['text']

        games_list = espn.get_games_list(
            self.mens_womens,
            self.conference,
            self.conf_id,
            date(2014, 11, 1),
            date(2015, 3, 8),
            conf_teams
        )

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
