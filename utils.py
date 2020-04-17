#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mailer import mail_jet
from bs4 import BeautifulSoup
from datetime import datetime
from pythonjsonlogger import jsonlogger
from shutil import copyfile, make_archive
from typing import Union, List, Dict
from zipfile import ZipFile

import base64
import config
import csv
import daiquiri
import daiquiri.formatter
import json
import logging
import os
import random
import requests
import shutil
import sys
import time


now = datetime.strftime(datetime.now(), '%Y-%m-%d')
logfile = os.path.join(config.LOG_DIR, '{}_{}.{}'.format(config.LOG_FILENAME, now, config.LOG_FILENAME_EXT))

SESSION = None
RETRIES = 0


def setup_logger(name: str, level=logging.DEBUG):
    daiquiri.setup(level=level, outputs=(
        daiquiri.output.Stream(sys.stdout),
        daiquiri.output.RotatingFile(logfile, formatter=jsonlogger.JsonFormatter(
            fmt=config.LOG_FORMAT),
            level=level, max_size_bytes=config.LOG_MAX_SIZE_BYTES, backup_count=config.LOG_BACKUP_COUNT
        )
    ))
    logger = daiquiri.getLogger(name)
    return logger


def get_soup(url: str):
    global logger, SESSION, RETRIES

    if RETRIES == 3:
        return None
    try:
        if not SESSION:
            SESSION = requests.Session()
            SESSION.headers.update(config.HEADERS)
        r = SESSION.get(url)
        if r.status_code == 403:
            # mail_jet('Check script', 'Are you human? Please check.')
            time_gap()
            manual_check()
            return get_soup(url)
        else:
            RETRIES = 0
            return BeautifulSoup(SESSION.get(url, timeout=30).text, 'lxml')
    except Exception as e:
        RETRIES = RETRIES + 1
        logger.error(e)
        return get_soup(url)


def manual_check():
    global SESSION

    # mail_jet('Being blocked', 'Check it!')
    print()
    cookie = input('Paste cookie or ENTER: ')
    if cookie:
        SESSION.headers.update({'cookie': cookie})
    print()


def time_gap():
    for remaining in range(random.randint(1, 7), 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write('Resuming in {:2d}\t'.format(remaining))
        sys.stdout.flush()
        time.sleep(1)


def dump_data_to_csv(data: Union[List, Dict], full_path: str):
    global logger

    try:
        exists = os.path.isfile(full_path)
        with open(full_path, 'a+') as f:
            writer = csv.DictWriter(f, fieldnames=config.CSV_HEADERS)
            if not exists:
                writer.writeheader()
            if isinstance(data, dict):
                writer.writerow(data)
                logger.info(f'{data.get("id")} saved')
            elif isinstance(data, list):
                for o in data:
                    writer.writerow(o)
        return True
    except Exception as e:
        logger.error(f'Unable to save data - {e}')
        return False


def dump_data_to_json(obj: Dict, full_path: str):
    with open(full_path, 'w') as f:
        json.dump(obj, f)


def cache_source(source: str, full_path: str):
    with open(full_path, 'w') as f:
        f.write(source)


def csv_to_json(full_path: str):
    data = []
    with open(full_path, 'r') as c:
        reader = csv.DictReader(c)
        for r in reader:
            data.append(json.loads(json.dumps(r)))
    return data


def price_changed(data, previous_data):
    _id = data.get('id')
    _data = list(filter(lambda x: x.get('id') == _id, previous_data))[0]
    price = data.get('price')
    _price = _data.get('price')
    pricedown = data.get('pricedown')
    _pricedown = _data.get('pricedown')

    if price and _price:
        if (price != _price) or (pricedown != _pricedown):
            return True
    return False


def send_mail(full_path: str, fname: str, subj: str, body: str = None):
    body = body or 'Please see attached file.'
    b64 = b64_file(full_path)
    if b64:
        att = {
            "Content-type": "application/zip",
            "Filename": fname,
            "Base64Content": b64
        }
        ok = mail_jet(subj, body, att)
        if ok:
            logger.info(f'{fname} sent to mail.')


def prepare_send(MAIL_PRICE_CHANGES: List, MAIL_NEW_LISTINGS: List, MAIL_REMOVED_LISTINGS: List):
    global logger

    logger.info('Preparing changes to mail')

    # save data, dump then send email
    if MAIL_PRICE_CHANGES:
        csv_fname = f'{now}_Price_Updates.csv'
        csv_full_path = os.path.join(config.PRICE_CHANGES_LOC, now, csv_fname)
        d = dump_data_to_csv(MAIL_PRICE_CHANGES, csv_full_path)
        copy_json_files(
            MAIL_PRICE_CHANGES,
            os.path.join(config.DATA_LOC, now),
            os.path.join(config.PRICE_CHANGES_LOC, now)
        )
        z = zip_folder(os.path.join(config.PRICE_CHANGES_LOC, now), f'{now}_Price_Updates')
        if d and z:
            send_mail(f'/tmp/{now}_Price_Updates.zip', '{now}_Price_Updates.zip', 'Price changes')

    if MAIL_NEW_LISTINGS:
        csv_fname = f'{now}_New_Listings.csv'
        csv_full_path = os.path.join(config.NEW_LISTINGS_LOC, now, csv_fname)
        d = dump_data_to_csv(MAIL_NEW_LISTINGS, csv_full_path)
        copy_json_files(
            MAIL_NEW_LISTINGS,
            os.path.join(config.DATA_LOC, now),
            os.path.join(config.MAIL_NEW_LISTINGS, now)
        )
        z = zip_folder(os.path.join(config.MAIL_NEW_LISTINGS, now), f'{now}_New_Listings')
        if d and z:
            send_mail(f'/tmp/{now}_New_Listings.zip', '{now}_New_Listings.zip', 'New Listings')

    if MAIL_REMOVED_LISTINGS:
        fname = f'{now}_Removed_Listings.csv'
        full_path = os.path.join(config.REMOVED_LISTINGS_LOC, fname)
        dump_data_to_csv(MAIL_REMOVED_LISTINGS, full_path)
        send_mail(full_path, fname, '')

        csv_fname = f'{now}_Removed_Listings.csv'
        csv_full_path = os.path.join(config.REMOVED_LISTINGS_LOC, now, csv_fname)
        d = dump_data_to_csv(MAIL_REMOVED_LISTINGS, csv_full_path)
        copy_json_files(
            MAIL_REMOVED_LISTINGS,
            os.path.join(config.DATA_LOC, now),
            os.path.join(config.MAIL_REMOVED_LISTINGS, now)
        )
        z = zip_folder(os.path.join(config.MAIL_REMOVED_LISTINGS, now), f'{now}_Removed_Listings')
        if d and z:
            send_mail(f'/tmp/{now}_Removed_Listings.zip', '{now}_Removed_Listings.zip', 'Removed Listings')


def copy_json_files(data: List, folder_from: str, folder_to: str):
    global logger

    for d in data:
        _id = d.get('id')
        try:
            shutil.copy(f'{folder_from}/{_id}.json', f'{folder_to}/{_id}.json')
        except Exception as e:
            logger.error(e)


def zip_file(full_path: str, fname: str):
    if os.path.isfile(full_path):
        with ZipFile(f'/tmp/{fname}.zip', 'w') as z:
            z.write(full_path)
        return True
    return False


def zip_folder(d: str, fname: str):
    global logger

    if os.path.exists(d):
        try:
            make_archive(f'/tmp/{fname}', 'zip', d)
            logger.info('/tmp/{} - Archive created'.format(fname))
            return True
        except Exception as e:
            logger.error('/tmp/{} - Unable to create archive - {}'.format(fname, e))
            return False
    return False


def b64_file(full_path: str):
    global logger

    try:
        with open(full_path, 'rb') as f:
            b = base64.b64encode(f.read())
        return b
    except Exception as e:
        logger.error(e)
    return None


def create_dir(d: str):
    if not os.path.exists(d):
        os.mkdir(d)


create_dir(config.DATA_LOC)
create_dir(os.path.join(config.DATA_LOC, now))
create_dir(config.LOG_DIR)
create_dir(config.PRICE_CHANGES_LOC)
create_dir(os.path.join(config.PRICE_CHANGES_LOC, now))
create_dir(config.NEW_LISTINGS_LOC)
create_dir(os.path.join(config.NEW_LISTINGS_LOC, now))
create_dir(config.REMOVED_LISTINGS_LOC)
create_dir(os.path.join(config.REMOVED_LISTINGS_LOC, now))
create_dir(config.CACHE_LOC)
create_dir(os.path.join(config.CACHE_LOC, now))

logger = setup_logger(__name__)
