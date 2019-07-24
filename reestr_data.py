import os
import pandas as pd
from gossluzhba_req import req_head, dwnld
from reestr_pdf_parser import parse_table
from mail_bot import send_mail, bodybuilder
import json
import schedule
import time
import numpy as np
from datetime import datetime
import re


def checker(file_name):
    verhis = json.loads(open("versions_history.json").read())
    if verhis:
        if not file_name in verhis:
            return verhis[-1]
    return None

def save_ver(file_name):
    verhis = json.loads(open("versions_history.json").read())
    verhis.append(file_name)
    with open("versions_history.json", "w") as f:
        f.write(json.dumps(verhis))


def find_diff(df1, df2, how):
    f_d = pd.merge(df1, df2, how=how, indicator='Exist')
    f_d = f_d.loc[f_d['Exist'] != 'both']
    del f_d['Exist']
    return f_d


def differ(df1, df2):
    df1 = df1[['full_name', 'date_npa', 'date_publishing']]
    df2 = df2[['full_name', 'date_npa', 'date_publishing']]
    add = find_diff(df1, df2, 'left')
    dell = find_diff(df1, df2, 'right')
    return list(add['full_name'].values), list(dell['full_name'].values)


def reas_str(df):
    gr=df.groupby('next_del_reason')
    t = ''
    for g in gr.groups:
        t+='\n'+g+':\n'+'\n'.join(gr.get_group(g)['full_name'].values)+'\n'
    return t


def get_future(df):
    date = '^\d+\s\w+\s\d{4}\sг\.'
    parts = re.compile(r'('+date+')\s(.+$)')

    fu_df = df[~df.date_publishing.str.contains(date+'$',
                                                regex=True,
                                                na=False)]
    anno = None
    if not fu_df.empty:
        fu_df = fu_df.assign(next_del_reason = fu_df['date_publishing'].replace(parts, r'\2'))
        fu_df.loc[:, 'date_publishing'] = fu_df['date_publishing'].replace(parts, r'\1')

        df = df.assign(next_del_reason = fu_df['next_del_reason'])
        df.loc[fu_df['date_publishing'].index, 'date_publishing'] = fu_df.loc[:,'date_publishing']

        anno = reas_str(fu_df)

    return df, anno


def csver(file_name, file_path):
    csv_file_name = file_name.replace('.pdf', '.csv')
    csv_file_path = os.path.join('csv_base', csv_file_name )
    return csv_file_name, csv_file_path


def updater():
    file_name, link, date = req_head()
    file_path = os.path.join('pdf_base', file_name)
    csv_file_name, csv_file_path = csver(file_name, file_path)
    flag = True

    che = checker(file_name)

    if che:

        dwnld(file_path, link)
        DATA = parse_table(file_path)
        DATA, announcement = get_future(DATA)

        DATA.to_csv(csv_file_path, index=False)

        che_path = os.path.join('csv_base', che.replace('.pdf', '.csv'))
        CHEDATA = pd.read_csv(che_path)

        diff_add, diff_del = differ(DATA, CHEDATA)

        return date, flag, announcement, diff_add, diff_del, csv_file_path, csv_file_name, file_name

    return date, flag, None, None, None, csv_file_path, csv_file_name, None


def reestr_update():
    # try:
    date, flag, announcement, diff_add, diff_del, csv_file_path, csv_file_name, file_name = updater()

    send_mail(date,
              flag,
              announcement,
              diff_add,
              diff_del,
              csv_file_path,
              csv_file_name)
    
    if file_name:
        save_ver(file_name)

    # except:
    #     send_mail(date = datetime.now().strftime("%d.%m.%Y"),
    #               flag = False)

