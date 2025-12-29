
import os
from datetime import datetime, timedelta
import pandas as pd
import traceback

from cmesdata.third.maths import Jsp_API
print("国内外历史高频股票期货等数据下载前往“cmes-data.com”网站获取")
print("--------------------")

import requests
debug = 0
bTest = 0
bLogin = False
api = Jsp_API()
str_bg = "cmes-data.com"
token = ""
last_login_time = None
fu_autu_token = ''

def print_info():
    if debug == 1:
        traceback.print_exc()
    print("入参格式错误，或时间超限，请检查！")


def get_time():
    global bLogin
    strt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if strt > str_bg:
        bLogin = False
    time_str= strt.split(' ')[1]
    return strt, time_str

def login(token_str):
    global token, str_bg, bLogin, last_login_time, fu_autu_token
    now = datetime.now()
    if last_login_time is not None and (now - last_login_time).total_seconds() < 60:
        print("登录接口在程序启动后只需要调用一次，请不要频繁调用！")
        return 1

    token = token_str
    # 将内容转换为字符串列表
    if debug == 1:
        url = f"http://127.0.0.1:5000/api/interface/auth"
    else:
        url = f"https://cmes-data.com:8080/api/interface/auth"
    payload = {
        "token": token ,
        "type": "all"
    }

    bLogin = False
    str_token, str_tokens, str_bg = "", "", ""
    response = requests.post(url, json=payload)
    last_login_time = now
    data = response.json()
    if response.status_code == 200:
        if data.get('success') == True and 'data' in data:
            autu_token = data['data'].get('autu_token')
            fu_autu_token = data['data'].get('fu_autu_token')
            if autu_token == '' and fu_autu_token == '':
                print('您未开通接口权限或已到期，请前往cmes-data.com开通权限')
                return 0
            if ':' in autu_token:
                str_token = autu_token.split(':')[0]
                str_tokens = autu_token.split(':')[1]
                str_bg = data['data'].get('autu_url')
                api.connect(str_token, int(str_tokens))
                bLogin = True
                return 1
            else:
                return 0
        else:
            if data.get('error') == None:
                print("连接失败，请稍后重试")
            else:
                print(data.get('error'))
            return 0
    else:
        if data.get('error') == None:
            print("连接失败，请稍后重试")
        else:
            print(data.get('error'))
        return 0

def login_out():
    global bLogin
    bLogin = False
    api.disconnect()

def Init():
    if bLogin == False:
        print("请先使用token登录或前往cmes-data.com开通股票接口权限")
        return False
    return bLogin
    
def __select_market_code(code):
    code = str(code)
    if '.' in code:
        if code.split('.')[0] == 'SZ':
            return 0
        elif code.split('.')[0] == 'SH': 
            return 1
        else:
            return 2
    else:
        if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
            return 1
        if code[0] in ['8']:
            return 2
        return 0

def __select_code(code):
    code = str(code)
    if '.' in code:
        return code.split('.')[1]
    else:
        return code

def get_code(market):
    list_df = []
    i = 0
    if market == 1:
        i = 1000
    while 1:
        df = api.to_df(api.get_security_list(market, i))
        if len(df) <= 1 :
            break

        if len(df) > 0:
            df00 = df[df['code'].str[:2] == '00']
            df30 = df[df['code'].str[:2] == '30'] #300开头获取不到
            df60 = df[df['code'].str[:2] == '60']
            df68 = df[df['code'].str[:2] == '68']

            list_df.append(df00)
            list_df.append(df30)
            list_df.append(df60)
            list_df.append(df68)

        i = i + 1000
    df = ''
    if len(list_df) > 0:
        df = pd.concat(list_df)
        df = df.drop(['volunit', 'decimal_point'], axis=1)
        df = df.reset_index(drop=True)
    return df

def get_history_data(code, start_date, end_date, period, index=False):
    try:
        if (not Init()):
            return pd.DataFrame()
        periodDic = {'1min' : 8, '5min': 0, '15min': 1, '30min': 2, '60min': 3, 'D': 4, 'W': 5, 'M': 6}

        date1 = datetime.strptime(start_date, "%Y-%m-%d")
        date2 = datetime.now()
        # 计算日期差异
        n = (date2 - date1).days + 1

        date_list = []
        for i in range(n):
            if index == False:
                df_tem = api.to_df(api.get_security_bars(periodDic[period], __select_market_code(code), __select_code(code), i * 800, 800))
            else:
                df_tem = api.to_df(api.get_index_bars(periodDic[period], __select_market_code(code), __select_code(code), i * 800, 800))
            if df_tem.empty:
                break
            time_tem = df_tem.iloc[0].loc['datetime']
            time2 = datetime.strptime(time_tem, "%Y-%m-%d %H:%M")

            date_list.insert(0, df_tem)

            if time2 < date1:
                break

        data = pd.concat(date_list)

        if data.empty:
            return data

        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        new_time = end_date + timedelta(days=1)
        end_date = new_time.strftime('%Y-%m-%d')

        data = data[(data['datetime'] >= start_date) & (data['datetime'] <= end_date)]
        data = data[['datetime', 'open', 'high', 'low', 'close', 'vol', 'amount']]
        data['datetime'] = data['datetime'] + ':00'
        data = data.reset_index(drop=True)
        data.loc[data['vol'] < 0.1, 'vol'] = 0
        data.loc[data['amount'] < 0.1, 'amount'] = 0
        data.columns = ['时间', '开盘价', '最高价', '最低价', '收盘价', '成交量', '成交额']
        return data
    except:
        print_info()
        return pd.DataFrame()

def get_index_data(code, start_date, end_date, period):
    return get_history_data(code, start_date, end_date, period, index=True)

def get_real_hq(all_stock):
    try:
        if len(all_stock) > 80 or not Init():
            return pd.DataFrame()
        
        list_all = []
        for c in all_stock:
            list_all.append((__select_market_code(c), __select_code(c)))
        stocks = api.get_security_quotes(list_all)
        if stocks == None:
            print("传入参数中有代码错误或现在停盘的股票，请剔除")
            return pd.DataFrame()
        combined_df = pd.DataFrame(stocks)
        combined_df = combined_df.drop(
            ['market', 'active1', 'reversed_bytes0', 'reversed_bytes1',
            'cur_vol', 'reversed_bytes2', 'reversed_bytes3', 'reversed_bytes4', 'reversed_bytes5',
            'reversed_bytes6', 'reversed_bytes7', 'reversed_bytes8', 'reversed_bytes9',
            'active2'], axis=1)

        time_str, time_str2 = get_time()
        combined_df['servertime'] = time_str

        if (time_str2 < "09:30:00" or time_str2 > "15:03:00") or (time_str2 > "11:33:00" and time_str2 < "13:00:00"):
            return pd.DataFrame()
        combined_df.columns = ['代码', '价格','昨收价','开盘价','最高价','最低价', '时间', '成交量', '成交额', '总卖', '总买', '买一价', '卖一价', '买一量',
                            '卖一量',
                            '买二价', '卖二价', '买二量', '卖二量', '买三价', '卖三价', '买三量', '卖三量', '买四价',
                            '卖四价', '买四量', '卖四量', '买五价', '卖五价', '买五量', '卖五量', ]
        return combined_df
    except:
        print_info()
        return pd.DataFrame()

def get_real_kzz(all_stock):
    df = get_real_hq(all_stock)
    if df.empty:
        return df

    df['价格'] = df['价格'] * 0.01
    df['昨收价'] = df['昨收价'] * 0.01
    df['开盘价'] = df['开盘价'] * 0.01
    df['最高价'] = df['最高价'] * 0.01
    df['最低价'] = df['最低价'] * 0.01
    df['买一价'] = df['买一价'] * 0.01
    df['买二价'] = df['买二价'] * 0.01
    df['买三价'] = df['买三价'] * 0.01
    df['买四价'] = df['买四价'] * 0.01
    df['买五价'] = df['买五价'] * 0.01
    df['卖一价'] = df['卖一价'] * 0.01
    df['卖二价'] = df['卖二价'] * 0.01
    df['卖三价'] = df['卖三价'] * 0.01
    df['卖四价'] = df['卖四价'] * 0.01
    df['卖五价'] = df['卖五价'] * 0.01
    return df

def get_tick(code, date):
    if not Init():
        return pd.DataFrame()
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
        date = int(date.strftime("%Y%m%d"))
        df1 = api.to_df(api.get_history_transaction_data(__select_market_code(code), __select_code(code), 0, 5000, date))
        df2 = api.to_df(api.get_history_transaction_data(__select_market_code(code), __select_code(code), 2000, 5000, date))
        df3 = api.to_df(api.get_history_transaction_data(__select_market_code(code), __select_code(code), 4000, 5000, date))
        df = pd.concat([df3, df2, df1], ignore_index=True)
        df.columns = ['时间', '价格', '成交量', '买卖方向']
        return df
    except:
        print_info()
        return pd.DataFrame()

    


#--------------------------



###########







