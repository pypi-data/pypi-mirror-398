#!/usr/bin/env python
# -*- coding: utf-8 -*-


import threading
import time
from datetime import datetime
from collections import deque
from typing import List
import pandas as pd
from openctp_ctp import mdapi


cmes_instrument_ids = []

class MarketDataCache:
    FIELD_MAPPING = {
        'ExchangeInstID': '交易所合约代码',
        'ActionDay': '当前日期',
        'AskPrice1': '卖一价', 'AskPrice2': '卖二价', 'AskPrice3': '卖三价', 'AskPrice4': '卖四价', 'AskPrice5': '卖五价',
        'AskVolume1': '卖一量', 'AskVolume2': '卖二量', 'AskVolume3': '卖三量', 'AskVolume4': '卖四量', 'AskVolume5': '卖五量',
        'AveragePrice': '平均价',
        'BandingLowerPrice': '下轨价格',
        'BandingUpperPrice': '上轨价格',
        'BidPrice1': '买一价', 'BidPrice2': '买二价', 'BidPrice3': '买三价', 'BidPrice4': '买四价', 'BidPrice5': '买五价',
        'BidVolume1': '买一量', 'BidVolume2': '买二量', 'BidVolume3': '买三量', 'BidVolume4': '买四量', 'BidVolume5': '买五量',
        'ClosePrice': '收盘价',
        'CurrDelta': '当前Delta',
        'ExchangeID': '交易所代码',
        'HighestPrice': '最高价',
        'InstrumentID': '合约代码',
        'LastPrice': '最新价',
        'LowerLimitPrice': '跌停价',
        'LowestPrice': '最低价',
        'OpenInterest': '持仓量',
        'OpenPrice': '开盘价',
        'PreClosePrice': '昨收价',
        'PreDelta': '昨Delta',
        'PreOpenInterest': '昨持仓量',
        'PreSettlementPrice': '昨结算价',
        'SettlementPrice': '结算价',
        'TradingDay': '交易日',
        'Turnover': '成交额',
        'UpdateMillisec': '更新时间毫秒',
        'UpdateTime': '更新时间',
        'UpperLimitPrice': '涨停价',
        'Volume': '成交量',
    }

    FIELDS_TO_REMOVE = {'reserve1', 'reserve2', 'this', 'thisown'}

    STANDARD_COLUMN_ORDER = [
        '交易所合约代码', '当前日期', '交易日', '更新时间', '更新时间毫秒',
        '最新价', '平均价', '成交量', '持仓量',
        '卖一价', '卖二价', '卖三价', '卖四价', '卖五价',
        '卖一量', '卖二量', '卖三量', '卖四量', '卖五量',
        '买一价', '买二价', '买三价', '买四价', '买五价',
        '买一量', '买二量', '买三量', '买四量', '买五量',
        '开盘价', '最高价', '最低价', '收盘价',
        '跌停价', '涨停价', '昨收价', '昨结算价', '昨持仓量',
        '结算价',
        '当前Delta', '昨Delta', '成交额', '下轨价格', '上轨价格'
    ]
    
    def __init__(self, max_size=100000):
        self._lock = threading.RLock()
        self._tick_data = {}
        self.max_size = max_size
    
    def add_tick(self, code: str, tick_dict: dict):
        with self._lock:
            if code not in self._tick_data:
                self._tick_data[code] = deque(maxlen=self.max_size)
            self._tick_data[code].append(tick_dict)
    
    def _format_dataframe_to_chinese(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'ExchangeInstID' not in df.columns:
            if 'InstrumentID' in df.columns:
                df['ExchangeInstID'] = df['InstrumentID']
        else:
            if 'InstrumentID' in df.columns:
                mask = df['ExchangeInstID'].isna() | (df['ExchangeInstID'] == '') | (df['ExchangeInstID'].isnull())
                if mask.any():
                    df.loc[mask, 'ExchangeInstID'] = df.loc[mask, 'InstrumentID']

        cols_to_drop = [col for col in df.columns if col in self.FIELDS_TO_REMOVE]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        rename_dict = {k: v for k, v in self.FIELD_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        ordered_cols = [col for col in self.STANDARD_COLUMN_ORDER if col in df.columns]
        other_cols = [col for col in df.columns if col not in ordered_cols]
        final_order = ordered_cols + other_cols

        df = df[final_order]
        
        return df
    
    def format_tick_to_chinese(self, tick_dict: dict) -> pd.DataFrame:
        df = pd.DataFrame([tick_dict])
        return self._format_dataframe_to_chinese(df)
    
    def get_last_ticks(self, code_list: List[str], num: int = 1) -> pd.DataFrame:
        all_ticks = []
        with self._lock:
            for code in code_list:
                if code in self._tick_data:
                    ticks = list(self._tick_data[code])[-num:]
                    if ticks:
                        df = pd.DataFrame(ticks)
                        all_ticks.append(df)
        
        if not all_ticks:
            return pd.DataFrame()

        result_df = pd.concat(all_ticks, ignore_index=True)
        return self._format_dataframe_to_chinese(result_df)
    
    def get_last_minutes(self, code_list: List[str], num: int = 1) -> pd.DataFrame:
        all_minutes = []
        with self._lock:
            for code in code_list:
                if code not in self._tick_data or len(self._tick_data[code]) == 0:
                    continue
                
                ticks = list(self._tick_data[code])
                if not ticks:
                    continue
                
                df = pd.DataFrame(ticks)
                if 'UpdateTime' not in df.columns or 'LastPrice' not in df.columns:
                    continue

                today = datetime.now().strftime('%Y-%m-%d')
                df['datetime_str'] = today + ' ' + df['UpdateTime'].astype(str)
                df['datetime'] = pd.to_datetime(df['datetime_str'], errors='coerce')
                df['minute'] = df['datetime'].dt.floor('1min')

                minutes = []
                prev_volume = {}
                
                for minute, group in df.groupby('minute', sort=True):
                    if group.empty or pd.isna(minute):
                        continue
                    
                    first_tick = group.iloc[0]
                    last_tick = group.iloc[-1]

                    vol_start = first_tick.get('Volume', 0) or 0
                    vol_end = last_tick.get('Volume', 0) or 0
                    minute_key = str(minute)
                    
                    if minute_key in prev_volume:
                        volume = vol_end - prev_volume[minute_key]
                    else:
                        volume = vol_end - vol_start if vol_end >= vol_start else vol_end
                    
                    if volume < 0:
                        volume = vol_end
                    
                    prev_volume[minute_key] = vol_end

                    prices = group['LastPrice'].dropna()
                    if prices.empty:
                        continue

                    high_idx = prices.idxmax()
                    low_idx = prices.idxmin()
                    
                    minute_data = {
                        '交易所合约代码': code,
                        '时间': minute.strftime('%Y-%m-%d %H:%M:%S'),
                        '开盘价': float(prices.iloc[0]),
                        '最高价': float(prices.max()),
                        '最低价': float(prices.min()),
                        '收盘价': float(prices.iloc[-1]),
                        '成交量': int(volume),
                        '持仓量': float(last_tick.get('Turnover', 0) or 0),
                        '开盘价时间': str(first_tick.get('UpdateTime', '')),
                        '最高价时间': str(group.loc[high_idx, 'UpdateTime']) if high_idx in group.index else str(first_tick.get('UpdateTime', '')),
                        '最低价时间': str(group.loc[low_idx, 'UpdateTime']) if low_idx in group.index else str(first_tick.get('UpdateTime', '')),
                        '收盘价时间': str(last_tick.get('UpdateTime', '')),
                        '涨停价': float(last_tick.get('UpperLimitPrice', 0) or 0),
                        '跌停价': float(last_tick.get('LowerLimitPrice', 0) or 0),
                    }
                    minutes.append(minute_data)

                if minutes:
                    all_minutes.extend(minutes[-num:])

        if not all_minutes:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(all_minutes)
        if '交易所合约代码' in result_df.columns:
            cols = ['交易所合约代码'] + [col for col in result_df.columns if col != '交易所合约代码']
            result_df = result_df[cols]
        
        return result_df
    
    def get_last_day(self, code_list: List[str]) -> pd.DataFrame:
        all_data = []
        with self._lock:
            for code in code_list:
                if code in self._tick_data and len(self._tick_data[code]) > 0:
                    latest_tick = list(self._tick_data[code])[-1]
                    latest_tick['ExchangeInstID'] = code
                    all_data.append(latest_tick)
        
        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        required_fields = [
            'ExchangeInstID',
            'ActionDay',
            'LastPrice',
            'OpenPrice',
            'HighestPrice',
            'LowestPrice',
            'ClosePrice',
            'UpperLimitPrice',
            'LowerLimitPrice',
            'Volume',
            'OpenInterest',
            'PreOpenInterest',
            'PreClosePrice',
            'SettlementPrice',
            'PreSettlementPrice',
        ]
        existing_fields = [f for f in required_fields if f in df.columns]
        df = df[existing_fields]
        rename_dict = {k: v for k, v in self.FIELD_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        chinese_order = [
            '交易所合约代码', '当前日期', '最新价', '开盘价', '最高价', '最低价', '收盘价',
            '涨停价', '跌停价', '成交量', '持仓量', '昨持仓量', '昨收价', '结算价', '昨结算价'
        ]
        final_order = [col for col in chinese_order if col in df.columns]
        df = df[final_order]
        
        return df


class MarketDataSpi(mdapi.CThostFtdcMdSpi):
    
    def __init__(self, api, cache: MarketDataCache):
        super().__init__()
        self.api = api
        self.cache = cache
        self._bar_callback = None
        
    def OnFrontConnected(self):
        print("行情服务器连接成功")
        req = mdapi.CThostFtdcReqUserLoginField()
        req.UserID = ""
        req.Password = ""
        req.BrokerID = ""
        self.api.ReqUserLogin(req, 0)
        
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"登录失败: {pRspInfo.ErrorMsg}")
        else:
            print("登录成功，开始订阅行情")
            global cmes_instrument_ids
            instrument_ids = cmes_instrument_ids
            result = self.api.SubscribeMarketData([i.encode('utf-8') for i in instrument_ids], len(instrument_ids))
                
            print(f"✓ 订阅成功！返回码: {result}")
        
    def OnRtnDepthMarketData(self, pDepthMarketData):
        tick_dict = {}
        for attr in dir(pDepthMarketData):
            if not attr.startswith('_'):
                try:
                    value = getattr(pDepthMarketData, attr)
                    if not callable(value):
                        tick_dict[attr] = value
                except:
                    pass
        if 'InstrumentID' in tick_dict:
            code = tick_dict['InstrumentID']
            tick_dict['UpdateTime'] = tick_dict.get('UpdateTime', '')
            tick_dict['UpdateMillisec'] = tick_dict.get('UpdateMillisec', 0)
            if 'ExchangeInstID' not in tick_dict or not tick_dict.get('ExchangeInstID'):
                tick_dict['ExchangeInstID'] = code
            self.cache.add_tick(code, tick_dict)
            if self._bar_callback is not None:
                try:
                    df = self.cache.format_tick_to_chinese(tick_dict)
                    self._bar_callback(df)
                except Exception as e:
                    print(f"调用客户回调函数时出错: {e}")
    
    def register_bar_callback(self, callback):
        if callable(callback):
            self._bar_callback = callback
        else:
            raise ValueError("回调函数必须是可调用对象")

market_cache = MarketDataCache(max_size=100000)
_global_spi = None
_pending_callback = None


def subscribe_market_data():
    from cmesdata.stock import fu_autu_token
    if ':' not in fu_autu_token:
        print('您未开通接口权限或已到期，请前往cmes-data.com开通期货权限')
        return
    global _global_spi, _pending_callback
    api = mdapi.CThostFtdcMdApi.CreateFtdcMdApi()
    spi = MarketDataSpi(api, market_cache)
    _global_spi = spi
    tocken_mes_sdr = 'tcp:'
    if _pending_callback is not None:
        spi.register_bar_callback(_pending_callback)
        _pending_callback = None
    api.RegisterSpi(spi)
    api.RegisterFront(f"{tocken_mes_sdr}//{fu_autu_token.split(':')[0]}:{fu_autu_token.split(':')[1]}")
    api.Init()
    api.Join()

def subscribe_future_code(code_list):
    global cmes_instrument_ids
    cmes_instrument_ids = code_list
    thread = threading.Thread(target=subscribe_market_data, daemon=True)
    thread.start()
    time.sleep(1)

def get_real_tick(code_list: List[str], num: int = 1) -> pd.DataFrame:
    return market_cache.get_last_ticks(code_list, num)

def get_real_min(code_list: List[str], num: int = 1) -> pd.DataFrame:
    return market_cache.get_last_minutes(code_list, num)

def get_real_day(code_list: List[str]) -> pd.DataFrame:
    return market_cache.get_last_day(code_list)


def register_push_callback(callback):
    global _global_spi, _pending_callback
    if _global_spi is not None:
        _global_spi.register_bar_callback(callback)
    else:
        _pending_callback = callback


def onbar_test_cmes(df):
    print('收到行情推送')
    print(df.to_string())

if __name__ == "__main__":
    subscribe_future_code(['ag2601'])
    register_push_callback(onbar_test_cmes)
    while True:
        time.sleep(5)
        print('-------------------------------------------------------------------------------------------------')
        print(get_real_tick(['ag2601'], 1).to_string())
        print(len(get_real_tick(['ag2601'], 10000)))

        df = get_real_min(['ag2601'], 1000)
        print("get_real_min(['ag2601'], 10):")
        print(df.to_string())


