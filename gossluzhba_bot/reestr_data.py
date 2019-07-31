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


def checker(ver_name):
    """
    Проверка наличия новой версии в реестре и не пуст ли список версий
    """
    verhis = json.loads(open("versions_history.json").read())
    if verhis:
        if not ver_name in verhis:
            return True, verhis[-1]
        return True, False
    return False, False


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
    # return list(add['full_name'].values), list(dell['full_name'].values)
    return add, dell


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

        # anno = reas_str(fu_df)

    return df, fu_df


def ext_name(ver_name, ext):
    ext_file_name = ver_name+'.'+ext
    ext_file_path = os.path.join(ext+'_base', ext_file_name)
    return ext_file_name, ext_file_path


def excel_maker(xlsx_file_path ,DATA, announcement , diff_add=None, diff_del=None):
    writer = pd.ExcelWriter(xlsx_file_path, engine='xlsxwriter')

    DATA.to_excel(writer, sheet_name='Реестр')
    if type(diff_add) != type(None):
    	diff_add.to_excel(writer, sheet_name='Добавленные персоны')
    if type(diff_del) != type(None):
    	diff_del.to_excel(writer, sheet_name='Удалённые персоны')
    announcement.to_excel(writer, sheet_name='Будут удалены')

    writer.save()


def work(ver_name, file_name, link):
    file_path = os.path.join('pdf_base', file_name)

    csv_file_name, csv_file_path = ext_name(ver_name, 'csv')
    
    dwnld(file_path, link)
    DATA = parse_table(file_path)

    DATA.drop('ind', axis=1, inplace=True)
    DATA, announcement = get_future(DATA)

    DATA.to_csv(csv_file_path, index=False)

    return DATA, announcement


def updater():
    file_name, link, date = req_head()
    ver_name = re.sub(r'\.\w+$', '', file_name)
    xlsx_file_name, xlsx_file_path = ext_name(ver_name, 'xlsx')
    
    flag = True

    vh, che = checker(ver_name)

    if not vh:
        DATA, announcement = work(ver_name, file_name, link)
        excel_maker(xlsx_file_path, DATA, announcement)

        return date, flag, None, None, None, xlsx_file_path, xlsx_file_name, ver_name

    if vh and che:

        DATA, announcement = work(ver_name, file_name, link)

        che_path = os.path.join('csv_base', che+'.csv')
        CHEDATA = pd.read_csv(che_path)

        diff_add, diff_del = differ(DATA, CHEDATA)
        
        excel_maker(xlsx_file_path, DATA, announcement , diff_add, diff_del)

        return date, flag, announcement, diff_add, diff_del, xlsx_file_path, xlsx_file_name, ver_name

    return date, flag, None, None, None, xlsx_file_path, xlsx_file_name, None



def fold(path):
    if not os.path.exists(path):
        os.mkdir(path)


def reestr_update():

    fold("csv_base")
    fold("pdf_base")
    fold("xlsx_base")

    # try:
    date, flag, announcement, diff_add, diff_del, xlsx_file_path, xlsx_file_name, ver_name = updater()

    send_mail(date,
              flag,
              announcement,
              diff_add,
              diff_del,
              xlsx_file_path,
              xlsx_file_name)

    if ver_name:
        save_ver(ver_name)

    # except:
    #     send_mail(date = datetime.now().strftime("%d.%m.%Y"),
    #               flag = False)

