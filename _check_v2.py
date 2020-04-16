import csv
import os
import simplejson as json
from pathlib import Path

if not os.path.exists('to_parse.txt'):
    Path('to_parse.txt').touch()

IDS = [i.strip() for i in open('to_parse.txt').readlines() if i.strip()]


def csv_to_json(full_path):
    data = []
    with open(full_path, 'r') as c:
        reader = csv.DictReader(c)
        for r in reader:
            data.append(json.loads(json.dumps(r)))
    return data


def parse_json_file(id):
    try:
        with open(f'files/#CHANGEME_DATE/{id}.json', 'r') as f:
            return json.loads(json.loads(f.read()))
    except Exception:
        return None


def write_ids(id):
    with open('to_parse.txt', 'a+') as f:
        f.write(f'{id}\n')


json_data = csv_to_json('files/#CHANGEME_DATE/#CSV')

print('{:<10}{:<15}CorrelationID'.format('#', 'ID'))
for i, entry in enumerate(json_data):
    d_id = 'TO PARSE'
    d_guid = ''
    for attribute, value in entry.items():
        d_id = entry['id']
        d_title = entry['title']
        d_price = entry['price']
        d_listed = entry['listed']
        d_status = entry['status']
        utag = parse_json_file(d_id)
        if not isinstance(utag, dict):
            if d_id not in IDS:
                write_ids(d_id)
                IDS.append(d_id)
            continue
        d_guid = utag.get('correlation', {}).get('id')
    print('{:<5}{:<15}{}'.format(i + 1, d_id, d_guid))

# Run after the above
# python main.py --file to_parse.txt
