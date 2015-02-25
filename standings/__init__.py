__version__ = '0.1.0'

from .basketball import BasketballStandings
import sys


def main():
    """
    The main entry point for the CLI.
    """
    if len(sys.argv) > 1:
        b = BasketballStandings('mens', sys.argv[1])
    else:
        b = BasketballStandings('mens', None)
    b.run()

if __name__ == '__main__':
    main()