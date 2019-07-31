from tabula.wrapper import read_pdf
import pandas as pd


def all_one(file_path, columns):
    """
    Convert pdf table to DataFrame wholly
    """
    df = read_pdf(
        file_path,
        # encoding='windows-1251',
        encoding='utf-8',
        lattice=True,
        pandas_options={'header': columns},
        pages='all'
    )
    
    return df
    
    
def col_name(old, new):
    return {e[0]:e[1] for e in list(zip(old, new))}


def multiple(file_path, columns):
    """
    Convert pdf table by pages
    """
    DATA = pd.DataFrame(columns=list(range(0,7)))
    tables = read_pdf(
        file_path,
        # encoding='windows-1251',
        encoding='utf-8',
        lattice=True,
        pandas_options={'header': None},
        pages='all',
        multiple_tables=True
    )
    
    for t in tables: # Because of mistakes while pasring we need to delete empty columns sometimes

        if t.shape[1] > 7:
            t.dropna(axis='columns', how='all', inplace=True) 
            # This solution works only if there is at least one full row on the page
            t.rename(
                columns=col_name(t.keys(), list(range(0,7))),
                inplace=True
            )
            continue
        
        DATA = DATA.append(t, ignore_index=True)
    
    DATA.rename(
        columns=col_name(DATA.keys(), columns),
        inplace=True
        )
    DATA.drop(0, inplace=True)

    return DATA


def wow(data, i):
    """
    Join separated rows in DataFrame
    """
    data.loc[i-1] = data.loc[i-1].combine(data.loc[i], lambda a, b: a+' '+b)
    data.drop(i, inplace = True)


def parse_table(file_path):
    columns=[
    'ind',
    'full_name',
    'organization',
    'role',
    'npa',
    'date_npa',
    'date_publishing'
    ]

    try:
        DATA = all_one(file_path, columns)
    except:
        DATA = multiple(file_path, columns)
        
    DATA = DATA.replace(regex=r'\r', value=' ') # В замена пробельного символа '\r' во всей таблице
    DATA = DATA.fillna('')
    DATA.loc[:,'ind'] = DATA['ind'].astype(str)
    for i in DATA[DATA['ind'] == ''].index.values[::-1]:
        wow(DATA, i)
    DATA.reset_index(drop=True, inplace=True)
    DATA['ind'] = DATA['ind'].astype(float).astype(int)
    DATA['full_name'] = DATA['full_name'].str.strip()
    DATA['date_npa'] = DATA['date_npa'].str.strip()
    DATA['date_publishing'] = DATA['date_publishing'].str.strip()

    return DATA
    