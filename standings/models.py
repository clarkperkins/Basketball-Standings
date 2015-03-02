
from .db import Base
from sqlalchemy import Column, Integer, String, ForeignKey


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


class Game(Base):
    date = Column(String)
    home_team_id = Column(ForeignKey(Team.id))
    away_team_id = Column(ForeignKey(Team.id))
    status = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    headline_url = Column(String)
