import pywaves as pw
import requests
import argparse
import json
import time
import os
try:
	import configparser
except ImportError:
	import ConfigParser as configparser

#configuration
cfg = {
    'node' : '',
    'apikey' : '',
    'checkassetid' : '',
    'top' : 0,
    'interval' : 300
}

def read_config(cfg_file):
    if not os.path.isfile(cfg_file):
        print("Missing config file")
        print("Exiting.")
        exit(1)

    global cfg
    try:
        print("Reading config file '{0}'".format(cfg_file))
        config = configparser.RawConfigParser()
        config.read(cfg_file)
        cfg['node'] = config.get('node', 'snapshotnode')
        cfg['apikey'] = config.get('node', 'apikey')

        cfg['checkassetid'] = config.get('snapshot', 'checkassetid')
        cfg['top'] = config.getint('snapshot', 'top')
        cfg['exclude'] = config.get('snapshot', 'excluded')

        cfg['interval'] = config.getint('main', 'interval')
        cfg['files'] = config.getint('main', 'number_of_files')

    except OSError:
        print("Error reading config file")
        print("Exiting.")
        exit(1)

def richlist(assetId, top):
    blockheight = requests.get(cfg['node'] + '/blocks/height').json()

    if assetId == 'WAVES':
        states = requests.get(cfg['node'] + '/debug/state/' + str(blockheight['height']), headers={ "api_key": cfg['apikey']}).json()
    elif assetId == 'TN':
        states = requests.get(cfg['node'] + '/debug/stateTN/' + str(blockheight['height']), headers={ "api_key": cfg['apikey']}).json()
    else:
        states = requests.get(cfg['node'] + '/assets/' + assetId + '/distribution', headers={ "api_key": cfg['apikey']}).json()

    n = 0
    for i in sorted(states.items(), key=lambda x: -x[1]):
        balance = i[1]
        if len(i[0]) == 35 and balance > 0:
            address = i[0]
            if address not in cfg['exclude']:
                n += 1
                richlisters.append({'address' : address, 'balance' : balance})

            if n == top and top != 0:
                break

def main():
    read_config('config.cfg')
    global richlisters

    n = 1
    while n <= cfg['files']:
        richlisters = []
        richlist(cfg['checkassetid'], cfg['top'])

        with open('richlist_' + str(n) + '.json', 'w') as outfile:
            json.dump(richlisters, outfile)

        n += 1
        if n > cfg['files']:
            break

        time.sleep(cfg['interval'])

if __name__ == "__main__":
    main()
