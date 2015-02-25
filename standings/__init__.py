__version__ = '0.1.0'

from .basketball import BasketballStandings
import sys


def main():
    """
    The main entry point for the CLI.
    """
    if len(sys.argv) < 2:
        print 'usage: {0} [mens|womens] [conference]'.format(sys.argv[0])
    elif len(sys.argv) > 2:
        b = BasketballStandings(sys.argv[1], sys.argv[2])
    else:
        b = BasketballStandings(sys.argv[1], None)
    b.run()

if __name__ == '__main__':
    main()