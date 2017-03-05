
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import sessionmaker


Session = sessionmaker()


class Base(object):
    # Always add an ID
    id = Column(Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


# Turn it into a real base class
Base = declarative_base(cls=Base)
