# Basketball-Standings

A python command-line interface for calculating college basketball conference standings


## Installation

The easiest way to install is using pip:

```bash
pip install git+https://github.com/clarkperkins/Basketball-Standings.git
```

OR

```bash
git clone https://github.com/clarkperkins/Basketball-Standings.git
pip install ./Basketball-Standings
```

## Usage

After installation, you will get a `basketball-standings` command added to your path.

```bash
> basketball-standings -h
usage: basketball-standings [-h] mens_womens [conference]

Get basketball standings

positional arguments:
  mens_womens  choose mens or womens basketball
  conference   the conference code

optional arguments:
  -h, --help   show this help message and exit
```

Running this command will print out the standings for the selected conference.
