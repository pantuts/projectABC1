#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import os
import simplejson as json
from pathlib import Path

if not os.path.exists('to_parse.txt'):
    Path('to_parse.txt').touch()

IDS = [i.strip() for i in open('to_parse.txt').readlines() if i.strip()]

p = argparse.ArgumentParser()
p.add_argument('--dir', help='Directory where the saved CSV and JSON files are.', type=str)
p.add_argument('--csv', help='CSV filename.', type=str)
args = p.parse_args()
work_dir = args.dir
csv_file = args.csv
if not work_dir or not csv_file:
    exit()


def csv_to_json(full_path):
    data = []
    with open(full_path, 'r') as c:
        reader = csv.DictReader(c)
        for r in reader:
            data.append(json.loads(json.dumps(r)))
    return data


def parse_json_file(id, d):
    try:
        with open(f'{d}/{id}.json', 'r') as f:
            return json.loads(json.loads(f.read()))
    except Exception:
        return None


def write_ids(id):
    with open('to_parse.txt', 'a+') as f:
        f.write(f'{id}\n')


json_data = csv_to_json(csv_file)

print('{:<10}{:<15}CorrelationID'.format('#', 'ID'))
for i, entry in enumerate(json_data):
    d_id = 'TO PARSE'
    d_guid = ''
    d_price = ''
    for attribute, value in entry.items():
        d_id = entry['id']
        d_title = entry['title']
        d_price = entry['price']
        d_listed = entry['listed']
        d_status = entry['status']
        utag = parse_json_file(d_id, work_dir)
        if not isinstance(utag, dict):
            if d_id not in IDS:
                write_ids(d_id)
                IDS.append(d_id)
            continue
        d_guid = utag.get('correlation', {}).get('id')
    print('{:<10}{:<15}{:<40}{}'.format(i + 1, d_id, d_guid, d_price))

# Run after the above
# python main.py --file to_parse.txt
