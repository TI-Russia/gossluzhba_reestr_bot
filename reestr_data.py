import os
import pandas as pd
from gossluzhba_req import req_head, dwnld
from reestr_pdf_parser import parse_table
from mail_bot import send_mail, bodybuilder
import json
import schedule
import time
import numpy as np


def checker(file_name):
    verhis = json.loads(open("versions_history.json").read())
    if verhis:
        if not file_name in verhis:
            verhis.append(file_name)
            with open("versions_history.json", 'w') as f:
                f.write(json.dumps(verhis))
            return verhis[-2]
    return None


def differ(a, b):
    c = a[(~a['full_name'].isin(b['full_name']))|
          (~a['date_npa'].isin(b['date_npa']))|
          (~a['npa'].isin(b['npa']))]
    diff_names = list(c['full_name'].values)
    if len(diff_names) > 0:
        return diff_names
    return None


def saver(DATA, file_name):
    DATA.to_csv(os.path.join('csv_base', file_name.replace('.pdf', '.csv')), index=False)
    DATA.to_json(os.path.join('json_base', file_name.replace('.pdf', '.json')))


def reestr_update():
    file_name, link, date = req_head()
    file_path = os.path.join('pdf_base', file_name)
    diff_add = None
    diff_del = None
    che = checker(file_name)
    if che:

        dwnld(file_path, link)
        DATA = parse_table(file_path)
        saver(DATA, file_name)

        che_path = os.path.join('csv_base', che.replace('.pdf', '.csv'))
        CHEDATA = pd.read_csv(che_path)

        diff_add = differ(DATA, CHEDATA)
        diff_del = differ(CHEDATA, DATA)
    
    send_mail(file_name.replace('.pdf', '.csv'), date, diff_add, diff_del)
