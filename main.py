#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime
from profile import Profile
from typing import List
from utils import setup_logger, get_soup, dump_data_to_csv, price_changed, prepare_send, csv_to_json
import argparse
import config
import glob
import os
import random
import re
import sys
import time

logger = setup_logger(__name__)
now = datetime.strftime(datetime.now(), '%Y-%m-%d')
CSV_FNAME = f'{now}_Listings.csv'

SEARCH_URL = config.SEARCH_URL
MAIN_URL = config.MAIN_URL


def get_profiles(soup: BeautifulSoup):
    return [MAIN_URL + a.get('href') for a in soup.find_all('a', class_='item-link', attrs={'href': re.compile(r'/inmueble')})]


def get_total_profiles(soup: BeautifulSoup):
    try:
        return int(soup.find('h1').get_text().strip().split()[0].replace('.', ''))
    except Exception:
        return None


def page_done(soup: BeautifulSoup):
    li = soup.find('li', class_='next')
    span = soup.find('span', text=re.compile(r'Siguiente'))
    if not li or not span:
        return True
    return False


def get_id(url: str):
    return re.findall(r'/([0-9].+)\/', url)[0]


def get_json_data():
    latest = sorted(glob.glob(os.path.join(config.DATA_LOC, '*.csv')), key=os.path.getmtime)
    if latest:
        latest = latest[-1]
        return csv_to_json(latest)
    return []


def get_existing_ids(data: List):
    return [i.get('id') for i in data]


def time_gap():
    for remaining in range(random.randint(1, 7), 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write('Resuming in {:2d}\t'.format(remaining))
        sys.stdout.flush()
        time.sleep(1)


if '__name__==__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--skip-ids', help='Skip just scraped IDs and do not compare data.', action='store_true')
    p.add_argument('--skip-data', help='Do not parse previous data', action='store_true')
    args = p.parse_args()
    skip_data = args.skip_data
    skip_ids = args.skip_ids or skip_data

    TOTAL_PROFILES_COUNT = None
    CURRENT_PROFILES_COUNT = 0
    CURRENT_PAGE = 1

    EXISTING_DATA = [] if skip_data else get_json_data()
    LISTING_IDS = get_existing_ids(EXISTING_DATA)
    CURRENT_IDS = LISTING_IDS.copy() if skip_ids else []

    # array of objects
    MAIL_PRICE_CHANGES = []
    MAIL_NEW_LISTINGS = []
    MAIL_REMOVED_LISTINGS = []

    while True:
        logger.info(f'--------------------------{CURRENT_PAGE}--------------------------')

        if TOTAL_PROFILES_COUNT and (CURRENT_PROFILES_COUNT >= TOTAL_PROFILES_COUNT):
            break

        soup = get_soup(SEARCH_URL.format(CURRENT_PAGE))
        if soup:
            if not TOTAL_PROFILES_COUNT:
                TOTAL_PROFILES_COUNT = get_total_profiles(soup)

            profiles = get_profiles(soup)
            if profiles:
                CURRENT_PROFILES_COUNT = CURRENT_PROFILES_COUNT + len(profiles)
                for url in profiles:
                    _id = get_id(url)
                    if _id in CURRENT_IDS:
                        continue

                    time_gap()

                    p_soup = get_soup(url)
                    if p_soup:
                        profile = Profile(url, p_soup)
                        data = profile.data
                        if not data.get('title'):
                            logger.error('Profile parse error {}'.format(url))
                            continue

                        if _id in LISTING_IDS:
                            pc = price_changed(data, EXISTING_DATA)
                            if pc:
                                data['status'] = 'price updated'
                                logger.info(f'{_id} price changed')
                                MAIL_PRICE_CHANGES.append(data)
                        else:
                            if LISTING_IDS:
                                data['status'] = 'new listing'
                                logger.info(f'{_id} new listing')
                                MAIL_NEW_LISTINGS.append(data)

                        dump_data_to_csv(data, os.path.join(config.DATA_LOC, CSV_FNAME))

                        CURRENT_IDS.append(_id)
            done = page_done(soup)
            if done:
                break
        else:
            # means reset page number
            if CURRENT_PROFILES_COUNT < TOTAL_PROFILES_COUNT:
                CURRENT_PAGE = CURRENT_PAGE - 1

        CURRENT_PAGE = CURRENT_PAGE + 1
        time_gap()

    removed = list(filter(lambda _id: _id not in CURRENT_IDS, LISTING_IDS))
    _removed = list(filter(lambda obj: obj.get('id') in removed, EXISTING_DATA))
    for r in _removed:
        r['status'] = 'removed'
    MAIL_REMOVED_LISTINGS = _removed.copy()

    prepare_send(MAIL_PRICE_CHANGES, MAIL_NEW_LISTINGS, MAIL_REMOVED_LISTINGS)
