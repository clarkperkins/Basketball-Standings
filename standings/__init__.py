
from standings.espn import ESPN


def main():
    espn = ESPN('ndzryyg4bp4zvjd43h7azdcp')

    sports = espn.get_leagues('basketball')

    print sports


if __name__ == '__main__':
    main()