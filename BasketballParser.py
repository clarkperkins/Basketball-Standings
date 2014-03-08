# An HTMLParser to parse basketball standings from ESPN

from HTMLParser import HTMLParser

class BasketballParser(HTMLParser):
    teams_in_conf = {}
    table_number = 0
    in_table = False
    get_team = False
    cur_class_data = ""
    results = []
    future_games = []
    get_future_game = False
    in_future_game_tag = False
    get_future_team = False
    future_game = []
    games_in_progress = []
    
    def __init__(self, teams):
        HTMLParser.__init__(self)
        self.teams_in_conf = teams
        self.table_number = 0
        self.in_table = False
        self.get_team = False
        self.results = []
        self.future_games = []
        self.get_future_game = False
        self.in_future_game_tag = False
        self.get_future_team = False
        self.future_game = []
        self.games_in_progress = []
    
    
    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table_number is 0:
            self.table_number += 1
            self.in_table = True
        #        elif self.in_table:
        #            print tag, "with attrs", attrs
        elif self.in_table and tag == "tr":
            for attr in attrs[0]:
                if "team" in attr:
                    self.get_team = True
                    self.cur_class_data = attr
        elif self.get_future_game and tag == "td":
            self.in_future_game_tag = True
            self.get_future_game = False
        elif self.in_future_game_tag and tag == "a":
            self.get_future_team = True
    
    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif self.in_future_game_tag and tag == "td":
            self.in_future_game_tag = False
    
    def handle_data(self, data):
        if self.get_team:
            #            pass
            if ',' in data:
                class_data = self.cur_class_data.split(" ")
                id1 = int(class_data[1].split("-")[2])
                id2 = int(class_data[2].split("-")[2])
                if id1 not in self.teams_in_conf.keys() or id2 not in self.teams_in_conf.keys():
                    return
                split_data = data.split(", ")
                new_data = []
                for i in split_data:
                    split2 = i.split(" ")
                    if "OT" in split2[len(split2)-1]:
                        split2.pop()
                    if "#" in split2[0]:
                        del split2[0]
                    split2.pop()
                    new_data.append(" ".join(split2).replace("AM","A&M"))
                #                print new_data
                self.results.append(new_data)
            #                print data
            #                print self.cur_class_data
            elif ':' in data:
                self.get_future_game = True
            self.get_team = False
        elif self.get_future_team:
            if ',' in data:
                self.games_in_progress.append(data.replace("AM","A&M"))
                self.get_future_team = False
            else:
                self.future_game.append(data.replace("AM", "A&M"))
                self.get_future_team = False
                if len(self.future_game) is 2:
                    self.future_games.append(self.future_game)
                    self.future_game = []
