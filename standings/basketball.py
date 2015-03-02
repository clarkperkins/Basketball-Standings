from datetime import date, timedelta
import os

from tabulate import tabulate
from sqlalchemy import create_engine

from .util import Utils
from .parsers import StandingsParser, ConferencesParser, GamesParser
from .models import Conference, Team, Game
from .db import Base, Session

# Grab the db file location
DB_FILE = os.environ.get('BASKETBALL_DB',
                         os.path.expanduser(os.path.join('~', '.basketball', 'db.sqlite')))

# Create the directory if it's not there
DB_DIR = os.path.dirname(DB_FILE)
if not os.path.isdir(DB_DIR):
    os.makedirs(DB_DIR)

utils = Utils()


class BasketballApp(object):
    """

    """
    def __init__(self, mens_womens, conference):
        super(BasketballApp, self).__init__()

        self.mens_womens = mens_womens
        self.conference = conference
        self.conf_id = None
        self.standings_dict = None
        self.team_ids = None
        self.future_games = None

        self.conferences_parser = ConferencesParser(self.mens_womens)
        self.games_parser = GamesParser()
        self.standings_parser = None

        # Create the db engine & tables
        self.engine = create_engine('sqlite:///%s' % DB_FILE)
        Base.metadata.create_all(self.engine)

        # Create the db session
        Session.configure(bind=self.engine)
        self.session = Session()

    def validate_input(self):
        db_conf = self.session.query(Conference).filter_by(slug=self.conference).first()

        if not db_conf or self.session.query(Conference).count() == 0:
            # Only load things if they're not already in the db
            conferences = self.conferences_parser.parse()
            for conf in conferences:
                db_conf = self.session.query(Conference).get(conf['confId'])
                if db_conf:
                    db_conf.id = conf['confId']
                    db_conf.name = conf['name']['text']
                    db_conf.slug = conf['slug']
                else:
                    # Insert the conference if it's not already here
                    self.session.add(Conference(
                        id=conf['confId'],
                        name=conf['name']['text'],
                        slug=conf['slug'],
                    ))

            self.session.commit()

        conferences = self.session.query(Conference).all()

        if not self.conference:
            print 'Conference choices: '
            for conf in conferences:
                print '   ', conf.slug
            exit(1)

        if self.conference not in map(lambda x: x.slug, conferences):
            print 'Invalid conference:', self.conference
            exit(1)

        for conf in conferences:
            if conf.slug == self.conference:
                self.conf_id = conf.id
                break

    def get_standings(self):
        self.standings_parser = StandingsParser(self.mens_womens, self.conf_id)

        standings = self.standings_parser.parse()

        self.standings_dict = {}

        for team in standings:
            db_team = self.session.query(Team).get(team['teamId'])
            if db_team:
                db_team.id = team['teamId']
                db_team.name = team['team']['text']
                db_team.conference_id = int(self.conf_id)
                db_team.conf_wins = team['conf_wins']
                db_team.conf_losses = team['conf_losses']
                db_team.overall_wins = team['overall_wins']
                db_team.overall_losses = team['overall_losses']
                db_team.streak = team['streak']
            else:
                self.session.add(Team(
                    id=team['teamId'],
                    name=team['team']['text'],
                    conference_id=int(self.conf_id),
                    conf_wins=team['conf_wins'],
                    conf_losses=team['conf_losses'],
                    overall_wins=team['overall_wins'],
                    overall_losses=team['overall_losses'],
                    streak=team['streak'],
                ))
            self.standings_dict[team['teamId']] = team

        self.session.commit()

        self.team_ids = map(lambda x: x['teamId'], standings)

    def get_games_for_date(self, game_date):
        """
        Pulls all the games for today from ESPN.
        :param game_date:
        :return:
        """
        print 'Fetching', game_date.strftime('%Y%m%d')

        games_parser = GamesParser(game_date.strftime('%Y%m%d'))

        games = games_parser.parse()

        for game in games:
            db_game = self.session.query(Game).filter_by(
                home_team_id=game['home_team']['teamId'],
                away_team_id=game['away_team']['teamId'],
            ).first()

            if db_game:
                db_game.status = game['status']
                db_game.home_score = game['home_score']
                db_game.away_score = game['away_score']
                db_game.headline_url = game['headline']['href']
            else:
                self.session.add(Game(
                    date=game_date.strftime('%Y%m%d'),
                    home_team_id=game['home_team']['teamId'],
                    away_team_id=game['away_team']['teamId'],
                    status=game['status'],
                    home_score=game['home_score'],
                    away_score=game['away_score'],
                    headline_url=game['headline']['href'],
                ))

        self.session.commit()

    def get_today_games(self):
        """

        :return:
        """
        self.get_games_for_date(date.today())

    def get_past_games(self):
        """

        :return:
        """
        today = date.today()
        year = today.year if today.month >= 11 else today.year - 1

        # Get all the games in the db that are final - then find the date of the last one and
        # start from there
        games = self.session.query(Game).filter(Game.status.like('%Final%')).order_by(Game.date).all()

        if len(games) == 0:
            cur_date = date(year, 11, 1)
        else:
            # start from the last date in the db
            cur_date_str = games[-1].date
            cur_date = date(int(cur_date_str[0:4]), int(cur_date_str[4:6]), int(cur_date_str[6:8]))

        while cur_date < today:
            self.get_games_for_date(cur_date)
            cur_date += timedelta(1)

    def get_future_games(self):
        """

        :return:
        """
        cur_date = date.today() + timedelta(1)
        final_date = date(2015, 3, 7)

        games = self.session.query(Game).filter(Game.date == cur_date.strftime('%Y%m%d')).all()

        if len(games) > 0:
            # the games are already here, so stop
            return

        while cur_date <= final_date:
            self.get_games_for_date(cur_date)
            cur_date += timedelta(1)

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
        self.get_past_games()
        self.get_future_games()
        self.get_today_games()

        conf_games = self.session.query(Game).filter(Game.home_team_id.in_(self.team_ids),
                                                     Game.away_team_id.in_(self.team_ids)).all()

        past_games = []
        future_games = []
        for game in conf_games:
            if 'Final' in game.status:
                if game.home_score > game.away_score:
                    winner = game.home_team_id
                    loser = game.away_team_id
                else:
                    winner = game.away_team_id
                    loser = game.home_team_id
                past_games.append((winner, loser))
            else:
                future_games.append((game.away_team_id, game.home_team_id))

        team_records = utils.get_win_loss_matrix(past_games)

        max_len = 0
        num_games = 0
        for i in team_records.keys():
            if len(self.standings_dict[i]['team']['text']) > max_len:
                max_len = len(self.standings_dict[i]['team']['text'])
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

        this_order = utils.order(team_records, True)

        print
        print "Current Conference Standings:"

        num = 1

        for team in this_order:
            print repr(num).rjust(2), \
                self.session.query(Team).get(team).name.\
                    ljust(max_len+1), \
                utils.record(team_records, team)
            num += 1

        print
        print

        # print "There are", len(games_in_progress), "games in progress."
        # for game in games_in_progress:
        #     print game

        print
        print "There are", len(future_games), "games left."

        if 0 < len(future_games) <= 21:
            for game in future_games:
                print self.session.query(Team).get(game[0]).name, "@", self.session.query(Team).get(game[1]).name

            possible_standings = utils.get_future_statistics(past_games, future_games)

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
                print self.session.query(Team).get(team).name.ljust(max_len + 1),
                for percent in possible_percents[team]:
                    if percent == 0.0:
                        print "    -",
                    else:
                        print ("%.1f" % percent).rjust(5),
                print

            print
