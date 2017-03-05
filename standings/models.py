
from .db import Base, Session
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean


class Conference(Base):
    name = Column(String)
    slug = Column(String)


class Team(Base):
    name = Column(String)
    conference_id = Column(ForeignKey(Conference.id))
    conf_wins = Column(Integer)
    conf_losses = Column(Integer)
    overall_wins = Column(Integer)
    overall_losses = Column(Integer)
    streak = Column(String)

    @property
    def conference(self):
        return Session().query(Conference).get(self.conference_id)


class Game(Base):
    date = Column(String)
    home_team_id = Column(ForeignKey(Team.id))
    away_team_id = Column(ForeignKey(Team.id))
    status = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    conference_game = Column(Boolean)

    @property
    def away_team(self):
        return Session().query(Team).get(self.away_team_id)

    @property
    def home_team(self):
        return Session().query(Team).get(self.home_team_id)
