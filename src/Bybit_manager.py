import time

import numpy as np
import pandas as pd
from dataclasses import dataclass
from src.logger import logging
from src.exception import CustomException
import os
import sys
import os
from src.utils import *
from datetime import datetime as dt
from datetime import timedelta
from pybit.unified_trading import HTTP
import streamlit as st
import threading
import warnings
warnings.filterwarnings('ignore')
data_list = []


@dataclass
class BybitConfig:
    bybit_intervals = [1, 3, 5, 15, 30, 60, 120, 240, 360, 720, 'D', 'M', 'W']

class BybitConnector:
    def __init__(self):
        # self.__session = HTTP(
        #     testnet=False,
        #     api_key="F3WEeuwW3WlId2p5oH",
        #     api_secret="2vnufofSJFc2ucl2lcdBoAedECHjaMwr4NUy",
        # )
        self.__session = HTTP(testnet=True)
        self._one_minute_value_in_ms = 60000
        self._one_day_value_in_ms = 86400000

    @staticmethod
    def date_to_millis(date_time: dt=None, *args) -> int:
        """
        Date to Millis
        :param: year, month, day, hour, minute, sec:
        :param: date_time:
        :return millis:
        """
        try:
            if date_time is None and args is not None:
                date = dt(*args)
                date_obj = date.timestamp()
                millis = int(date_obj * 1000)
                return millis
            else:
                date_obj = date_time.timestamp()
                millis = int(date_obj * 1000)
                return millis
        except Exception as e:
            logging.error('date to millis error ', str(e))
            raise CustomException(e, sys)

    @staticmethod
    def millis_to_date(value: int, ret_type='datetime') -> dt or str:
        """
        Millis to date
        :param value: millis value:
        :param ret_type: str or datetime:
        :return:
        """
        try:
            seconds = value / 1000
            date = dt.fromtimestamp(seconds)
            if ret_type == 'str':
                return date.strftime('%d/%b/%Y %H:%M:%S.%f %p')
            elif ret_type == 'datetime':
                return date
        except Exception as e:
            logging.error('millis to date error ', str(e))
            raise CustomException(e, sys)

    @staticmethod
    def get_datetime(DateTime: dt = None, *args, **kwargs) -> Dict or dt or None:
        """
        DateTime default option None gives current datetime as dictionary
        DateTime validates datetime object and returns it as dictionary
        DateTime validates year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        :param DateTime: datetime object:
        :param args:
        :param kwargs:
        :return:
        """
        date = {}
        if DateTime is None and args is None and kwargs is None:
            date['day'] = int(dt.now().strftime('%d'))
            date['month'] = int(dt.now().strftime('%m'))
            date['year'] = int(dt.now().strftime('%Y'))
            date['hour'] = int(dt.now().strftime('%H'))
            date['minute'] = int(dt.now().strftime('%M'))
            date['second'] = int(dt.now().strftime('%S'))
            date['milsec'] = int(dt.now().strftime('%f'))
            return date
        elif DateTime is not None and type(DateTime) == dt:
            date['day'] = int(DateTime.strftime('%d'))
            date['month'] = int(DateTime.strftime('%m'))
            date['year'] = int(DateTime.strftime('%Y'))
            date['hour'] = int(DateTime.strftime('%H'))
            date['minute'] = int(DateTime.strftime('%M'))
            date['second'] = int(DateTime.strftime('%S'))
            date['milsec'] = int(DateTime.strftime('%f'))
            return date
        else:
            try:
                if args:
                    return dt(*args)
                elif kwargs:
                    return dt(**kwargs)
            except:
                return None

    def get_open_interest(
            self, start_date_time_in_mils, category="inverse", symbol="BTCUSD", interval_time="30min"
    ) -> float or None:
        """
        Gets open interest from bybit
        :param start_date_time_in_mils:
        :param category: Product type. spot,linear,inverse:
        :param symbol:
        :param interval_time: 1,3,5,15,30,60,120,240,360,720,D,M,W:
        :return open interest:
        """
        try:
            open_interest_data = self.__session.get_open_interest(
                category=category, symbol=symbol, intervalTime=interval_time, startTime=start_date_time_in_mils,
                endTime=start_date_time_in_mils + 1740000,
            )
            oi = float(open_interest_data['result']['list'][0]['openInterest'])
            logging.info(f'Open interest {oi}')
            return oi
        except Exception as e:
            logging.debug(f'Open interest not found {e}')
            return None

    def get_market_data(self, start_date_time_in_mils, end_date_time_in_mils, category="inverse",
                        symbol="BTCUSD", interval=30) -> Dict or None:
        """
        Gets market data or kline data
        :param interval: 1,3,5,15,30,60,120,240,360,720,D,M,W::
        :param start_date_time_in_mils:
        :param end_date_time_in_mils:
        :param category: Product type. spot,linear,inverse:
        :param symbol:
        :return:
        """
        try:
            market_data = self.__session.get_kline(
                category=category, symbol=symbol, interval=interval, start=start_date_time_in_mils, end=end_date_time_in_mils
            )
            data_list = market_data['result']['list']
            df_list = []
            for item in data_list:
                df_list.append({
                    'Start Time': pd.to_datetime(int(item[0]), unit='ms'),
                    'Open': float(item[1]),
                    'High': float(item[2]),
                    'Low': float(item[3]),
                    'Close': float(item[4]),
                    'Volume': float(item[5]),
                    'Turnover': float(item[6]),
                })
            return df_list[-1]
        except Exception as e:
            logging.debug(f'Data not found {e}')
            return None


class CheckAndExecuteTrade(BybitConnector):
    def __init__(self, start_datetime, end_datetime, interval, tp_percent=0.25, sl_percent=0.5):
        super().__init__()
        self.start_datetime = start_datetime
        self.start_datetime_dic = self.get_datetime(start_datetime)
        self.end_datetime = end_datetime
        self.end_datetime_dic = self.get_datetime(end_datetime)
        self.start_year = self.start_datetime_dic['year']
        self.start_month = self.start_datetime_dic['month']
        self.start_day = self.start_datetime_dic['day']
        self.start_hour = self.start_datetime_dic['hour']
        self.start_min = self.start_datetime_dic['minute']
        self.start_time_millis = (self.start_hour * 60 * 60000) + (self.start_min * 60000)
        self.end_year = self.end_datetime_dic['year']
        self.end_month = self.end_datetime_dic['month']
        self.end_day = self.end_datetime_dic['day']
        self.end_hour = self.end_datetime_dic['hour']
        self.end_min = self.end_datetime_dic['minute']
        self.end_time_millis = (self.end_hour * 60 * 60000) + (self.end_min * 60000)
        self.ib_high = 0  # Initial Balance high
        self.ib_low = 0  # Initial Balance low
        self.tp_percent = tp_percent # Take Profit
        self.sl_percent = sl_percent # Stop Loss
        self.interval = interval
        self.serial_number = 1

    def check_short_trade(self) -> None:
        """
        Short trade checks if previous high price is in between current high and current close and executes short trade
        """
        count = 0
        start_date_time_in_mills = self.date_to_millis(date_time=self.start_datetime)
        end_date_time_in_mills = self.date_to_millis(date_time=self.end_datetime)

        market_data = self.get_market_data(start_date_time_in_mills, start_date_time_in_mills, interval=self.interval)
        if market_data is not None:
            high_price = market_data['High']
            cur_date_time_in_mills = start_date_time_in_mills
            while cur_date_time_in_mills < end_date_time_in_mills:
                cur_hour = self.millis_to_date(cur_date_time_in_mills).hour
                cur_min = self.millis_to_date(cur_date_time_in_mills).minute
                cur_time_millis = (cur_hour * 60 * 60000) + (cur_min * 60000)
                if cur_time_millis > self.end_time_millis:
                    cur_date_time_in_mills = self.date_to_millis(self.millis_to_date(
                        cur_date_time_in_mills).replace(hour=self.start_hour, minute=self.start_min) +
                                                                 timedelta(days=1))
                cur_market_data = self.get_market_data(
                    cur_date_time_in_mills, cur_date_time_in_mills, interval=self.interval
                )
                if cur_market_data is not None:
                    data = {}
                    data["Check No"] = self.serial_number
                    data["Date"] = self.millis_to_date(cur_date_time_in_mills, ret_type='datetime').strftime(
                        '%d/%b/%Y')
                    data["Day"] = self.millis_to_date(cur_date_time_in_mills, ret_type='datetime').strftime("%a")
                    data["Trade Type"] = "Short"
                    data['Interval'] = self.interval
                    data["IB_H"] = cur_market_data['High']
                    data["IB_L"] = cur_market_data['Low']
                    data["IB%"] = np.round(
                        (
                                (cur_market_data['High'] - cur_market_data['Low']
                                 ) / cur_market_data['Low']) * 100, 2
                    )
                    data['Volume'] = cur_market_data['Volume']
                    data['Turnover'] = cur_market_data['Turnover']
                    print(f'Checking for short trade, count {count}, '
                          f'at {self.millis_to_date(cur_date_time_in_mills, ret_type="str")}')

                    oi = self.get_open_interest(cur_date_time_in_mills)
                    if oi:
                        data['Open Interest'] = oi
                        print(f'Open Interest {oi}')

                    if cur_market_data['High'] > high_price > cur_market_data['Close']:
                        print("Condition for a short Trade Have been Found Executing Short Trade - Entry Price: ",
                              cur_market_data["Close"], "Executed at ",
                              (self.millis_to_date(cur_date_time_in_mills, ret_type='str')))
                        short_data = self.execute_short_trade(cur_market_data['Close'], cur_date_time_in_mills)
                        if short_data is not None:
                            short_data["Entry Price"] = cur_market_data['Close']
                            short_data["Entry Time"] = str(self.millis_to_date(cur_date_time_in_mills, ret_type='str'))
                            data.update(short_data)
                            data_list.append(data)
                            cur_date_time_in_mills = self.date_to_millis(self.millis_to_date(
                                cur_date_time_in_mills).replace(hour=self.start_hour, minute=self.start_min) +
                                                      timedelta(days=1))

                    cur_date_time_in_mills += (self._one_minute_value_in_ms * self.interval)
                    self.serial_number += 1
                    count += 1

    def check_for_long_trade(self) -> None:
        """
        Long trade checks if previous low price is in between current close and current low and executes long trade
        """
        count = 0
        start_date_time_in_mills = self.date_to_millis(date_time=self.start_datetime)
        end_date_time_in_mills = self.date_to_millis(date_time=self.end_datetime)

        market_data = self.get_market_data(start_date_time_in_mills, start_date_time_in_mills, interval=self.interval)
        if market_data is not None:
            low_price = market_data['Low']
            cur_date_time_in_mills = start_date_time_in_mills
            while cur_date_time_in_mills < end_date_time_in_mills:
                cur_hour = self.millis_to_date(cur_date_time_in_mills).hour
                cur_min = self.millis_to_date(cur_date_time_in_mills).minute
                cur_time_millis = (cur_hour * 60 * 60000) + (cur_min * 60000)
                if cur_time_millis > self.end_time_millis:
                    cur_date_time_in_mills = self.date_to_millis(self.millis_to_date(
                        cur_date_time_in_mills).replace(hour=self.start_hour, minute=self.start_min) +
                                                                 timedelta(days=1))
                cur_market_data = self.get_market_data(
                    cur_date_time_in_mills, cur_date_time_in_mills, interval=self.interval
                )
                if cur_market_data is not None:
                    data = {}
                    data["Count No"] = self.serial_number
                    data["Date"] = self.millis_to_date(cur_date_time_in_mills, ret_type='datetime').strftime(
                        '%d/%b/%Y')
                    data["Day"] = self.millis_to_date(cur_date_time_in_mills, ret_type='datetime').strftime("%a")
                    data["Trade Type"] = "Long"
                    data['Interval'] = self.interval
                    data["IB_H"] = cur_market_data['High']
                    data["IB_L"] = cur_market_data['Low']
                    data["IB%"] = np.round(
                        (
                                (cur_market_data['High'] - cur_market_data['Low']
                                 ) / cur_market_data['Low']) * 100, 2
                    )
                    data['Volume'] = cur_market_data['Volume']
                    data['Turnover'] = cur_market_data['Turnover']
                    print(f'Checking for long trade, count {count}, '
                          f'at {self.millis_to_date(cur_date_time_in_mills, ret_type="str")}')

                    oi = self.get_open_interest(cur_date_time_in_mills)
                    if oi:
                        data['Open Interest'] = oi
                        print(f'Open Interest {oi}')
                    data['Volume'] = cur_market_data['Volume']
                    data['Turnover'] = cur_market_data['Turnover']
                    if cur_market_data['Close'] > low_price > cur_market_data['Low']:
                        print("Condition for a Long Trade Have been Found Executing Long Trade - Entry Price: ",
                              cur_market_data["Close"], "Executed at Time ",
                              (self.millis_to_date(cur_date_time_in_mills, ret_type='str')))
                        long_data = self.execute_long_trade(cur_market_data['Close'], cur_date_time_in_mills)
                        if long_data is not None:
                            long_data["Entry Price"] = cur_market_data['Close']
                            long_data["Entry Time"] = str(self.millis_to_date(cur_date_time_in_mills, ret_type='str'))
                            data.update(long_data)
                            data_list.append(data)
                            cur_date_time_in_mills = self.date_to_millis(self.millis_to_date(
                                cur_date_time_in_mills).replace(hour=self.start_hour, minute=self.start_min) +
                                                                         timedelta(days=1))

                    cur_date_time_in_mills += (self._one_minute_value_in_ms * self.interval)
                    self.serial_number += 1
                    count += 1

    def execute_short_trade(self, entry_price, start_date_time_in_mils) -> Dict or None:
        """
        Win situation:-
        While current low price less than (entry price - entry price * take profit percentage)

        Loss situation:-
        While current high price greater than (entry price + entry price * stop loss percentage)

        No trade situation:-
        While candel_start_date_time_in_ms is greater than (market data start time - one min value * 30) + one day value
        if current close price less than entry price it is win else it is loss
        """
        short_data = {}
        count = 1
        candel_start_date_time_in_ms = start_date_time_in_mils
        while True:
            cur_hour = self.millis_to_date(candel_start_date_time_in_ms).hour
            cur_min = self.millis_to_date(candel_start_date_time_in_ms).minute
            cur_time_millis = (cur_hour * 60 * 60000) + (cur_min * 60000)
            if cur_time_millis > self.end_time_millis:
                return None
            market_data = self.get_market_data(
                candel_start_date_time_in_ms, candel_start_date_time_in_ms, interval=self.interval
            )
            if market_data is not None:
                if market_data['Low'] < (float(entry_price) - (float(entry_price) * self.tp_percent)):
                    print("Winning Short Trade Day at " + str((dt.fromtimestamp(candel_start_date_time_in_ms / 1000))))

                    short_data["TP Price"] = float(float(entry_price) + (float(entry_price) * self.tp_percent))
                    short_data["TP Time"] = str(market_data['Start Time'])
                    short_data["SL Price"] = float(float(entry_price) - (float(entry_price) * self.sl_percent))
                    short_data["SL Time"] = " "
                    short_data["Win Loss No Trade"] = 1
                    short_data['Take Profit %'] = self.tp_percent
                    short_data['Stop Loss %'] = self.sl_percent
                    short_data["Total % Gain"] = np.round(
                        (((market_data['Low'] - entry_price) / entry_price) * 100) * 10, 2)
                    return short_data
                if market_data['High'] > (
                        float(entry_price) + (float(entry_price) * self.sl_percent)):
                    print("Loosing  Short Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))

                    short_data["TP Price"] = float(float(entry_price) + (float(entry_price) * self.tp_percent))
                    short_data["TP Time"] = " "
                    short_data["SL Price"] = float(market_data['Close'])
                    short_data["SL Time"] = str(market_data['Start Time'])
                    short_data["Win Loss No Trade"] = 0
                    short_data['Take Profit %'] = self.tp_percent
                    short_data['Stop Loss %'] = self.sl_percent
                    short_data["Total % Gain"] = np.round(
                        (((entry_price - market_data['High']) / entry_price) * 100) * 10, 2)
                    return short_data

                candel_start_date_time_in_ms += (self._one_minute_value_in_ms * self.interval)
                if candel_start_date_time_in_ms > (
                        (self.date_to_millis(market_data['Start Time']) - (self._one_minute_value_in_ms * 30)) +
                        self._one_day_value_in_ms):
                    print("Trade Never Reached TP and Next day has has arrived, Closing at: " +
                          str(market_data['Close']))

                    if market_data['Close'] < entry_price:
                        short_data["TP Price"] = float(market_data['Close'])
                        short_data["TP Time"] = str(market_data['Start Time'])
                        short_data["Win Loss No Trade"] = 1
                        short_data['Take Profit %'] = self.tp_percent
                        short_data['Stop Loss %'] = self.sl_percent
                    else:
                        short_data["SL Price"] = float((float(entry_price) + (float(entry_price) * self.sl_percent)))
                        short_data["SL Time"] = str(dt.fromtimestamp(candel_start_date_time_in_ms / 1000))
                        short_data["Win Loss No Trade"] = 0
                        short_data['Take Profit %'] = self.tp_percent
                        short_data['Stop Loss %'] = self.sl_percent
                    return short_data
                else:
                    print(f'Retrying to execute, Count {count}',
                          f'{self.millis_to_date(candel_start_date_time_in_ms, ret_type="str")}')
                    count += 1

    def execute_long_trade(self, entry_price, start_date_time_in_mils) -> Dict or None:
        """
        Win situation:-
        While current high greater than (entry price - entry price * take profit percentage)

        Loss situation:-
        While current low price less than (entry price + entry price * stop loss percentage)

        No trade situation:-
        while candel_start_date_time_in_ms greater than (market data start time - one min value * 30) + one day value
        if current close price less than entry price it is win else it is loss
        """

        long_data = {}
        count = 1
        candel_start_date_time_in_ms = start_date_time_in_mils
        while True:
            cur_hour = self.millis_to_date(candel_start_date_time_in_ms).hour
            cur_min = self.millis_to_date(candel_start_date_time_in_ms).minute
            cur_time_millis = (cur_hour * 60 * 60000) + (cur_min * 60000)
            if cur_time_millis > self.end_time_millis:
                return None
            market_data = self.get_market_data(
                candel_start_date_time_in_ms, candel_start_date_time_in_ms, interval=self.interval
            )
            if market_data is not None:
                if market_data['High'] > (float(entry_price) - (float(entry_price) * self.tp_percent)):
                    print("Winning Long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    long_data["TP Price"] = float(float(entry_price) + (float(entry_price) * self.tp_percent))
                    long_data["TP Time"] = str(market_data['Start Time'])
                    long_data["SL Price"] = float(float(entry_price) - (float(entry_price) * self.sl_percent))
                    long_data["SL Time"] = " "
                    long_data["Win Loss No Trade"] = 1
                    long_data['Take Profit %'] = self.tp_percent
                    long_data['Stop Loss %'] = self.sl_percent
                    long_data["Total % Gain"] = np.round(
                        (((market_data['Low'] - entry_price) / entry_price) * 100) * 10, 2)
                    return long_data
                if market_data['Low'] < (float(entry_price) + (float(entry_price) * self.sl_percent)):
                    print("Loosing  long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    long_data["TP Price"] = float(float(entry_price) + (float(entry_price) * self.tp_percent))
                    long_data["TP Time"] = " "
                    long_data["SL Price"] = float(market_data['Close'])
                    long_data["SL Time"] = str(market_data['Start Time'])
                    long_data["Win Loss No Trade"] = 0
                    long_data['Take Profit %'] = self.tp_percent
                    long_data['Stop Loss %'] = self.sl_percent
                    long_data["Total % Gain"] = np.round(
                        (((entry_price - market_data['High']) / entry_price) * 100) * 10, 2)
                    return long_data

                candel_start_date_time_in_ms += (self._one_minute_value_in_ms * self.interval)
                if candel_start_date_time_in_ms > (
                        (market_data['Start Time'] - (self._one_minute_value_in_ms * 30)) + self._one_day_value_in_ms):
                    print("Trade Never Reached TP and Next day has has arrived, Closing at: " +
                          str(market_data['Close']))
                    if market_data['Close'] < entry_price:
                        long_data["TP Price"] = float(market_data['Close'])
                        long_data["TP Time"] = str(market_data['Start Time'] / 1000)
                        long_data["Win Loss No Trade"] = 1
                        long_data['Take Profit %'] = self.tp_percent
                        long_data['Stop Loss %'] = self.sl_percent
                    else:
                        long_data["SL Price"] = float((float(entry_price) + (float(entry_price) * self.sl_percent)))
                        long_data["SL Time"] = str(dt.fromtimestamp(candel_start_date_time_in_ms / 1000))
                        long_data["Win Loss No Trade"] = 0
                        long_data['Take Profit %'] = self.tp_percent
                        long_data['Stop Loss %'] = self.sl_percent
                    return long_data

                else:
                    print(f'Retrying to execute, Count {count}',
                          f'{self.millis_to_date(candel_start_date_time_in_ms, ret_type="str")}')
                    count += 1

class InitiateBybitTrade(CheckAndExecuteTrade):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def check_for_both_long_and_short_trade(self) -> None:
        short_trade = threading.Thread(target=self.check_short_trade)
        long_trade = threading.Thread(target=self.check_for_long_trade)
        short_trade.start()
        long_trade.start()
        short_trade.join()
        long_trade.join()

    def bitcoin_trade(self, trade_selection,) -> pd.DataFrame:
        if trade_selection == 'Short':
            self.check_short_trade()
        elif trade_selection == 'Long':
            self.check_for_long_trade()
        elif trade_selection == 'Both':
            self.check_for_both_long_and_short_trade()
        return pd.DataFrame(data_list, index=None)


if __name__ == '__main__':
    try:
        pass
    except Exception as e:
        raise CustomException(e, sys)
