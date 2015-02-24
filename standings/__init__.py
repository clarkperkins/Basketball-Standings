__version__ = '0.1.0'

from .basketball import BasketballStandings
from .parser import GamesParser
import requests


def main():
    """
    The main entry point for the CLI.
    """
    # b = BasketballStandings('mens', 'sec')
    # b.run()

    c = GamesParser(50)

    for i in c.parse():
        print i
        print

if __name__ == '__main__':
    main()