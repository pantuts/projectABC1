#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv('.env')

DATA_LOC = './files'
PRICE_CHANGES_LOC = './files_price_changes'
NEW_LISTINGS_LOC = './files_new_listings'
REMOVED_LISTINGS_LOC = './files_removed_listings'
CACHE_LOC = './cache'

LOG_FORMAT = '%(asctime)s [PID %(process)d] [%(levelname)s] %(name)s -> %(message)s'
LOG_DIR = './logs'
LOG_FILENAME = 'logs'
LOG_FILENAME_EXT = 'json'
LOG_MAX_SIZE_BYTES = 1.5e+7  # 15mb
LOG_BACKUP_COUNT = 10

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'dnt': '1',
    'cookie': os.getenv('COOKIE')
}

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
NAME_FROM = os.getenv('NAME_FROM')
NAME_TO = os.getenv('NAME_TO')

CSV_HEADERS = [
	'id', 'title', 'meta_desc', 'listed', 'price',
	'pricedown', 'pricedown_percent', 'status', 'url', 'date_scraped'
]
SEARCH_URL = os.getenv('SEARCH_URL')
MAIN_URL = os.getenv('MAIN_URL')
PROFILE_URL = os.getenv('PROFILE_URL')
