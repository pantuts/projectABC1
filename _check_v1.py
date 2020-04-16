import csv
import os
import simplejson as json


def csv_to_json(full_path):
    data = []
    with open(full_path, 'r') as c:
        reader = csv.DictReader(c)
        for r in reader:
            data.append(json.loads(json.dumps(r)))
    return data


def parse_json_file(id):
    try:
        with open(f'{id}.json', 'r') as f:  # CHANGE ME
            return json.loads(json.loads(f.read()))
    except Exception:
        return None


json_data = csv_to_json('#CHANGEME')

print('{:<10}{:<15}CorrelationID'.format('#', 'ID'))
for i, entry in enumerate(json_data):
    d_id = ''
    d_guid = ''
    for attribute, value in entry.items():
        d_id = entry['id']
        d_title = entry['title']
        d_price = entry['price']
        d_listed = entry['listed']
        d_status = entry['status']
        utag = parse_json_file(d_id)
        d_guid = utag.get('correlation', {}).get('id')
    print('{:<5}{:<15}{}'.format(i + 1, d_id, d_guid))
