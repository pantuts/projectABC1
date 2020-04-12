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
import requests
import sys


now = datetime.strftime(datetime.now(), '%Y-%m-%d')
logfile = os.path.join(config.LOG_DIR, '{}_{}.{}'.format(config.LOG_FILENAME, now, config.LOG_FILENAME_EXT))

SESSION = None


def setup_logger(name: str, level=logging.DEBUG):
    global logger
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
    global logger, SESSION
    try:
        if not SESSION:
            SESSION = requests.Session()
            SESSION.headers.update(config.HEADERS)
        r = SESSION.get(url)
        if r.status_code == 403:
            # mail_jet('Check script', 'Are you human? Please check.')
            manual_check()
            return get_soup(url)
        return BeautifulSoup(SESSION.get(url, timeout=30).text, 'lxml')
    except Exception as e:
        logger.error(e)
        return None


def manual_check():
    global SESSION
    # mail_jet('Being blocked', 'Check it!')
    print()
    cookie = input('Paste cookie or ENTER: ')
    if cookie:
        SESSION.headers.update({'cookie': cookie})
    print()


def dump_data_to_csv(data: Union[List, Dict], full_path: str):
    global logger

    try:
        with open(full_path, 'a+') as f:
            writer = csv.DictWriter(f, fieldnames=config.CSV_HEADERS)
            if not os.path.isfile(full_path):
                writer.writeheader()
            if isinstance(data, dict):
                writer.writerow(data)
                logger.info(f'{data.get("id")} saved')
            elif isinstance(data, list):
                for o in data:
                    writer.writerow(o)
    except Exception as e:
        logger.error(f'Unable to save data - {e}')


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


def prepare_send(MAIL_PRICE_CHANGES: List, MAIL_NEW_LISTINGS: List, MAIL_REMOVED_LISTINGS: List):
    logger.info('Preparing changes to mail')

    # save data, compress then send email
    if MAIL_PRICE_CHANGES:
        fname = f'{now}_Price_Updates.csv'
        full_path = os.path.join(config.PRICE_CHANGES_LOC, fname)

        dump_data_to_csv(MAIL_PRICE_CHANGES, full_path)

        subj = 'Price changes'
        body = 'Please see attached file.'
        b64 = b64_file(full_path)
        if b64:
            att = {
                "Content-type": "text/csv",
                "Filename": fname,
                "Base64Content": b64
            }
            ok = mail_jet(subj, body, att)
            if ok:
                logger.info(f'{fname} sent to mail.')

    if MAIL_NEW_LISTINGS:
        fname = f'{now}_New_Listings.csv'
        full_path = os.path.join(config.NEW_LISTINGS_LOC, fname)

        dump_data_to_csv(MAIL_PRICE_CHANGES, full_path)

        subj = 'New Listings'
        body = 'Please see attached file.'
        b64 = b64_file(full_path)
        if b64:
            att = {
                "Content-type": "text/csv",
                "Filename": fname,
                "Base64Content": b64
            }
            ok = mail_jet(subj, body, att)
            if ok:
                logger.info(f'{fname} sent to mail.')

    if MAIL_REMOVED_LISTINGS:
        fname = f'{now}_Removed_Listings.csv'
        full_path = os.path.join(config.REMOVED_LISTINGS_LOC, fname)

        dump_data_to_csv(MAIL_PRICE_CHANGES, full_path)

        subj = 'Removed Listings'
        body = 'Please see attached file.'
        b64 = b64_file(full_path)
        if b64:
            att = {
                "Content-type": "text/csv",
                "Filename": fname,
                "Base64Content": b64
            }
            ok = mail_jet(subj, body, att)
            if ok:
                logger.info(f'{fname} sent to mail.')


def zip_file(full_path: str, fname: str):
    if os.path.isfile(full_path):
        with ZipFile(f'/tmp/{fname}.zip', 'w') as z:
            z.write(full_path)
        return True
    return False


def zip_folder(d: str, fname: str):
    if os.path.exists(d):
        try:
            make_archive(fname, 'zip', d)
            logger.info('/tmp/{} - Archived created'.format(fname))
            return True
        except Exception as e:
            logger.error('/tmp/{} - Unable to create archive - {}'.format(fname, e))
            return False
    return False


def b64_file(full_path: str):
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
create_dir(config.LOG_DIR)
create_dir(config.PRICE_CHANGES_LOC)
create_dir(config.NEW_LISTINGS_LOC)
create_dir(config.REMOVED_LISTINGS_LOC)

logger = setup_logger(__name__)
