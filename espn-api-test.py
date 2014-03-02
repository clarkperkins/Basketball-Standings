#!/usr/bin/env python

import requests, json

URL = "http://api.espn.com/v1"
API_KEY = "?apikey=ndzryyg4bp4zvjd43h7azdcp"

r = requests.get(URL+"/sports/basketball/mens-college-basketball"+API_KEY)

res = r.json()

#print json.dumps(res, indent=3)

#print len(res['sports'][0]['leagues'][0])

#for i in res['sports'][0]['leagues'][0]['groups'][0]['groups']:
#    print i['name']


#print res['sports']

#print len(res['sports'][0]['leagues'][0])

#print res['sports'][0]['leagues'][0]['name']

conferences = []
max_len = 0

for i in res['sports'][0]['leagues'][0]['groups'][0]['groups']:
    conferences.append({'name':i['name'], 'abbr':i['abbreviation'], 'id':i['groupId']})
    if len(i['name']) > max_len:
        max_len = len(i['name'])


for i in conferences:
    print i['name'].ljust(max_len+1), i['abbr']




