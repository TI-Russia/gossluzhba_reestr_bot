import requests
from bs4 import BeautifulSoup as bs
import re
import os
from fake_useragent import UserAgent
from urllib.parse import unquote
from transliterate import translit
from datetime import datetime


def no_russian(file_name):
    if re.search(r'[а-яё]', file_name):
        file_name = translit(file_name, 'ru', reversed=True)
    return file_name


def req_head():
    """
    Get link to current file and head request to get info about the file
    Return the file name and its link
    """
    main_page = 'https://gossluzhba.gov.ru/reestr'
    r = requests.get(main_page)
    r.raise_for_status()
    s = bs(r.text, 'lxml')
    link = s.find('a', href=re.compile(r'.+files\.gossluzhba\.gov\.ru.+'))['href']
    h = requests.head(link)
    h.raise_for_status()
    H = h.headers
    file_date = datetime.strptime(H['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z")
    date = file_date.strftime("%d.%m.%Y")
    file_name = unquote(re.search(r'%.+', H['Content-Disposition']).group())
    file_name = no_russian(file_name)
    return file_name, link, date


def dwnld(file_path, link):
    """
    Dowload the file to ./originals/
    """
    ua = UserAgent()
    headers = {'User-Agent': ua.random}   
    reestr = requests.get(link, headers=headers)

    with open(file_path, "wb") as f:
        f.write(reestr.content)