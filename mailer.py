#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mailjet_rest import Client
import config

mailjet = Client(auth=(config.API_KEY, config.API_SECRET), version='v3.1')

DATA = {
    'Messages': [
        {
            'From': {
                'Email': config.EMAIL_FROM,
                'Name': config.NAME_FROM
            },
            'To': [
                {
                    'Email': config.EMAIL_TO,
                    'Name': config.NAME_TO
                }
            ],
            'Subject': '',
            'TextPart': '',
            'Attachments': []
        }
    ]
}


def mail_jet(subj: str, body: str, att=None):
    DATA['Messages'][0]['Subject'] = subj
    DATA['Messages'][0]['TextPart'] = body
    if att:
        DATA['Messages'][0]['Attachments'] = att
    try:
        mailjet.send.create(data=DATA)
        return True
    except Exception as e:
        return False
