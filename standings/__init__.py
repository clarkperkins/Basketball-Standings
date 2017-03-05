from argparse import ArgumentParser

from .basketball import BasketballApp

__version__ = '0.1.0'


def main():
    """
    The main entry point for the CLI.
    """
    parser = ArgumentParser(description='Get basketball standings')

    parser.add_argument('mens_womens',
                        help='choose mens or womens basketball')

    parser.add_argument('conference',
                        nargs='?',
                        help='the conference code')

    args = parser.parse_args()

    try:
        app = BasketballApp(args.mens_womens, args.conference)
        app.run()
    except KeyboardInterrupt:
        exit(1)

if __name__ == '__main__':
    main()
