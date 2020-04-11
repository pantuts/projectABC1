#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime
import re


class Profile:
    def __init__(self, url: str, soup: BeautifulSoup):
        self.url = url
        self.soup = soup
        self.data = {
            'id': self.get_id(),
            'utag': self.get_utag(),
            'title': self.get_title(),
            'meta_desc': self.get_meta_desc(),
            'listed': self.get_listed(),
            'price': self.get_price(),
            'pricedown': self.get_pricedown_percent()[0],
            'pricedown_percent': self.get_pricedown_percent()[1],
            'status': 'listed',
            'url': url,
            'date_scraped': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        }

    def get_id(self):
        return re.findall(r'/([0-9].+)\/', self.url)[0]

    def get_utag(self):
        utag = re.findall(r'utag_data = (.+?\});', str(self.soup))
        return "{}".format(utag[0]) if utag else ''

    def get_title(self):
        try:
            return self.soup.find('head').find('title').get_text().strip()
        except Exception:
            return ''

    def get_meta_desc(self):
        try:
            return self.soup.find('head').find('meta', {'name': 'description'}).get('content').strip()
        except Exception:
            return ''

    def get_listed(self):
        try:
            p = BeautifulSoup(re.findall(r'Estadísticas.+(\<p\>Anuncio.+\</p\>)', str(self.soup))[0], 'lxml')
            return p.get_text().strip()
        except Exception:
            return ''

    def get_price(self):
        try:
            return self.soup.find('span', class_='info-data-price').get_text().replace('€', '').strip()
        except Exception:
            return ''

    def get_pricedown_percent(self):
        try:
            p = self.soup.find('span', class_='pricedown').get_text().replace('€', '').split()
            if len(p) == 2:
                return p[0].strip(), p[1].strip()
            return '', ''
        except Exception:
            return '', ''
