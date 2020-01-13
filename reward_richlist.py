import pywaves as pw
import csv
import json
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
import pywaves.crypto as crypto
import base58
import struct
import os
try:
	import configparser
except ImportError:
	import ConfigParser as configparser

#configuration
cfg = {
    'node' : 'https://privatenode2.blackturtle.eu',
    'network' : 'turtlenetwork',
    'matcher' : 'https://privatematcher.blackturtle.eu',
    'datafeed' : 'https://bot.blackturtle.eu',
    'orderfee' : 4000000,
    'rewardAssetID' : 'TN',
    'paymentsfile' : 'payments.json',
    'rewardamount' : 0.0001,
    'myprivateKey' : '',
    'dopayment' : 0,
    'amountfiles' : 9
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
        cfg['node'] = config.get('network', 'node')
        cfg['network'] = config.get('network', 'network')
        cfg['matcher'] = config.get('network', 'matcher')
        cfg['datafeed'] = config.get('network', 'datafeed')
        cfg['orderfee'] = config.getint('network', 'order_fee')

        cfg['myprivateKey'] = config.get('account', 'private_key')

        cfg['interval'] = config.getint('main', 'interval')
        cfg['rewardAssetID'] = config.get('main', 'rewardasset')
        cfg['paymentsfile'] = config.get('main', 'paymentsfile')
        cfg['rewardamount'] = config.getfloat('main', 'rewardamount')
        cfg['dopayment'] = config.getint('main', 'dopayment')
        cfg['amountfiles'] = config.getint('main', 'number_of_files')
    except OSError:
        print("Error reading config file")
        print("Exiting.")
        exit(1)

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def masspay(traders):
    global address
    global cfg

    print('number of payouts in batch: ' + str(len(traders)))
    print('paid from address: ' + address.address)
    print('paying in ' + cfg['rewardAssetID'] + ' !')

    txFee = cfg['orderfee'] + (1000000 * (len(traders) + 1))
    attachment = 'Pool Party Node Token montly airdrop reward airdrop!'
    mytimestamp = int(round(datetime.timestamp(datetime.now()) * 1000))
    transfersData = b''
    for i in range(0, len(traders)):
        transfersData += base58.b58decode(traders[i]['recipient']) + struct.pack(">Q", traders[i]['amount'])
    sData = b'\x0b' + \
            b'\1' + \
            base58.b58decode(address.publicKey) + \
            b'\0' + \
            struct.pack(">H", len(traders)) + \
            transfersData + \
            struct.pack(">Q", mytimestamp) + \
            struct.pack(">Q", txFee) + \
            struct.pack(">H", len(attachment)) + \
            crypto.str2bytes(attachment)

    signature = crypto.sign(address.privateKey, sData)

    data = json.dumps({
        "type": 11,
        "version": 1,
        "assetId": cfg['rewardAssetID'],
        "senderPublicKey": address.publicKey,
        "fee": txFee,
        "timestamp": mytimestamp,
        "transfers": traders,
        "attachment": base58.b58encode(crypto.str2bytes(attachment)),
        "signature": signature,
        "proofs": [
            signature
        ]
    })

    try:
        tx = pw.wrapper('/transactions/broadcast', data)
        print('payment done, txid: ' + str(tx['id']))
    except Exception as e:
        print("Exception ")
        print(str(e))

def checkconf():
    #check if the required stuff is in the cfg file
    global cfg

    return True

#initialization
read_config('config.cfg')

if checkconf == False:
    exit(1)

asset = pw.Asset(cfg['rewardAssetID'])
print("Richlist reward script started with the following configuration:")
print("-" * 80)
print("Interval is set to " + str(cfg['interval']) + " seconds.")
print(str(cfg['amountfiles']) + " snapshotfiles will be loaded.")
print("Richlist will receive " + str(cfg['rewardamount']) + " in " + str(asset.name) + ".") 

if cfg['dopayment'] == 1: print("Rewards will be payed automatically.")
else: print("Payments will be saved to " + cfg['paymentsfile'])

pw.setNode(cfg['node'], cfg['network'],'L')
address = pw.Address(privateKey = cfg['myprivateKey'])

#create list
richlist = defaultdict(dict)
total = 0

n = 1
while n <= cfg['amountfiles']:
    filename = 'richlist_' + str(n) + '.json'

    with open(filename, 'r') as f:
        load_richlist = json.load(f)

    for r in load_richlist:
        if r['address'] not in richlist:
            richlist[r['address']]['balance'] = int(r['balance'])
        else:
            richlist[r['address']]['balance'] = int(richlist[r['address']]['balance']) + int(r['balance'])

        total += int(r['balance'])

    n += 1

#calculate averages
total = total / cfg['amountfiles']

for r in richlist:
    avgamount = richlist[r]['balance'] / cfg['amountfiles']
    richlist[r]['perc'] = avgamount / total
    richlist[r]['reward'] = int((cfg['rewardamount'] * pow(10, asset.decimals)) * (avgamount / total))

#payments
payments = []
paynow = []
for r in richlist:
    payments.append({ 'amount': richlist[r]['reward'] * pow(10, asset.decimals), 'fee': cfg['orderfee'], 'sender': address.address, 'attachment': 'Pool Party Node Token montly airdrop reward airdrop!', 'recipient': r, 'assetId': cfg['rewardAssetID']})
    paynow.append({ 'amount': richlist[r]['reward'] * pow(10, asset.decimals), 'recipient': r})

if cfg['dopayment'] == 1:
    masspay(paynow)
else:
    try:
        with open(cfg['paymentsfile'], 'w') as outfile:
            json.dump(payments, outfile)
            print("Payments file created")
    except OSError:
        print("Error wrting payments file")
