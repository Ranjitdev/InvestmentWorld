import time

import numpy as np
import pandas as pd

from src.logger import logging
from src.exception import CustomException
import os
import sys
import os
from src.utils import *
from datetime import datetime as dt
from pybit.unified_trading import HTTP
import streamlit as st
import threading
stop_event = threading.Event()
import warnings
warnings.filterwarnings('ignore')

data = {
    "Sl No": " ",
    "Date": " ",
    "Day": " ",
    "Trade Type": " ",
    "IB_H": " ",
    "IB_L": " ",
    "IB%": " ",
    "Entry Price": " ",
    "Entry Time": " ",
    "SL Price": " ",
    "SL Time": " ",
    "TP Price": " ",
    "TP Time": " ",
    "Total % Gain": " ",
    "Win Loss No Trade": " "
}
serial_number = 1


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
    def date_to_millis(year, month, day, hour, minute, sec=0) -> int or str:
        """
        Date to Millis
        :param year:
        :param month:
        :param day:
        :param hour:
        :param minute:
        :param sec:
        :return millis:
        """
        try:
            date = dt(year, month, day, hour, minute, sec)
            date_obj = date.timestamp()
            millis = int(date_obj * 1000)
            return millis
        except Exception as e:
            logging.error('date to millis error ', str(e))
            raise CustomException(e, sys)

    @staticmethod
    def millis_to_date(value) -> dt or str:
        """
        Millis to date
        :param value:
        :return date:
        """
        try:
            seconds = value / 1000
            date = dt.fromtimestamp(seconds)
            return date.strftime('%d/%b/%Y %H:%M:%S.%f %p')
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
        if args is None and kwargs is None:
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

    def get_market_data(self, interval, start_date_time_in_mils, end_date_time_in_mils, category="inverse",
                        symbol="BTCUSD", interval_time="30min") -> Dict or None:
        """
        Gets market data or kline data
        :param interval:
        :param start_date_time_in_mils:
        :param end_date_time_in_mils:
        :param category: Product type. spot,linear,inverse:
        :param symbol:
        :param interval_time: 1,3,5,15,30,60,120,240,360,720,D,M,W:
        :return:
        """
        try:
            start_value = start_date_time_in_mils + (self._one_minute_value_in_ms * 30)
            # This is where one minute converts into 30 minutes for 6AM morning time
            end_value = end_date_time_in_mils + (self._one_minute_value_in_ms * 30)
            # This is where one minute converts into 30 minutes for 6AM morning time

            market_data = self.__session.get_kline(
                category=category, symbol=symbol, interval=interval, start=start_value, end=end_value
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
    def __init__(
            self, start_year, start_month, start_day, start_hour, start_minute, end_year, end_month, end_day, end_hour,
            end_min
    ):
        super().__init__()
        self.start_year = start_year
        self.start_month = start_month
        self.start_day = start_day
        self.start_hour = start_hour
        self.start_min = start_minute
        self.end_year = end_year
        self.end_month = end_month
        self.end_day = end_day
        self.end_hour = end_hour
        self.end_min = end_min
        self.ib_high = 0  # Initial Balance high
        self.ib_low = 0  # Initial Balance low
        self.tp_percent = 0.3 / 100  # 0.25% TP Take Profit
        self.sl_percent = 1.5 / 100  # 1.5% SL Stop Loss
        self.trade_setup = 0  # 0 - Only Short 1 - only long 2 - both long and short
        self.interval = 1
        self.valid_intervals = [1, 3, 5, 15, 30, 60, 120, 240, 360, 720, 'D', 'M', 'W']

    def check_short_trade(self, duration, sleep_time: int = 5) -> None:
        """
        Short trade checks if previous high price is in between current high and current close and executes short trade
        """
        start_time = time.time()
        global data
        global serial_number
        global stop_event
        message_container1 = st.empty()
        message_container2 = st.empty()
        message_container3 = st.empty()
        message_container4 = st.empty()
        message_container5 = st.empty()
        message_container6 = st.empty()
        count = 0
        start_date_time_in_mils = self.date_to_millis(
            self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0)
        six_am_candle_start_time = start_date_time_in_mils + (
                self._one_minute_value_in_ms * 30)
        # This is where one minute converts into 30 minutes for 6AM morning time

        market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
        if market_data is not None:
            high_price = market_data['High']
            low_price = market_data['Low']
            data["Sl.no"] = serial_number
            data["Date"] = dt(
                self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0
            ).strftime('%d/%b/%Y %H:%M:%S.%f %p')
            data["Day"] = dt(
                self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0
            ).strftime("%a")
            data["Trade Type"] = "Short"
            data["IB_H"] = str(high_price)
            data["IB_L"] = str(low_price)
            data["IB%"] = str(((float(high_price) - float(low_price)) / float(low_price)) * 100)

            while (time.time() - start_time) < duration:
                cur_market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
                if market_data is not None:
                    count += 1
                    print(f'Checking for short trade, count {count}')
                    message_container1.caption(
                        f'Checking for short trade at :green[{self.millis_to_date(start_date_time_in_mils)}], '
                        f'Check count :blue[{count}]'
                    )
                    oi = self.get_open_interest(start_date_time_in_mils)
                    if oi:
                        message_container2.caption(f'Open Interest: :green[{oi}]')
                    message_container3.dataframe(pd.DataFrame([cur_market_data]), hide_index=True)

                    if cur_market_data['High'] > high_price > cur_market_data['Close']:
                        print("Condition for a short Trade Have been Found Executing Short Trade - Entry Price: ",
                              cur_market_data["Close"], "Executed at ",
                              (self.millis_to_date(six_am_candle_start_time).strftime(
                                  '%d/%b/%Y %H:%M:%S.%f %p')))
                        message_container4.caption(
                            ":green[Condition for a short Trade Have been Found Executing Short Trade - Entry Price: ]",
                            cur_market_data['Close'], "Executed at ",
                            (self.millis_to_date(six_am_candle_start_time).strftime(
                                   '%d/%b/%Y %H:%M:%S.%f %p')))
                        self.execute_short_trade(cur_market_data['Close'])
                        logging.info('Short trade executed')
                        data["Entry Price"] = str(cur_market_data['Close'])
                        data["Entry Time"] = str(dt.fromtimestamp(six_am_candle_start_time / 1000))
                        break

                    six_am_candle_start_time += self._one_minute_value_in_ms
                    if six_am_candle_start_time > (start_date_time_in_mils + self._one_day_value_in_ms):
                        print("Short Trade Setup Never occurred, Setup will continue checking the next day")
                        message_container4.info(
                            "red[Short Trade Setup Never occurred, Setup will continue checking the next day]")
                        logging.info('Short trade not executed')
                        data["Entry Price"] = None
                        data["Entry Time"] = None
                        data["SL Price"] = None
                        data["SL Time"] = None
                        data["TP Price"] = None
                        data["TP Time"] = None
                        data["Total % Gain"] = None
                        data["Win Loss No Trade"] = None
                        break
                    message_container5.caption(
                        f'Countdown timer :blue[{np.round((duration - (time.time() - start_time)) / 60, 2)} min]')
                    message_container6.caption(dt.now().strftime('%d/%m/%Y %H:%M:%S.%f %p'))
                    serial_number += 1
                    time.sleep(sleep_time)

    def check_for_long_trade(self, duration, sleep_time: int = 5) -> None:
        """
        Long trade checks if previous low price is in between current close and current low and executes long trade
        """
        start_time = time.time()
        global data
        global serial_number
        global stop_event
        message_container1 = st.empty()
        message_container2 = st.empty()
        message_container3 = st.empty()
        message_container4 = st.empty()
        message_container5 = st.empty()
        message_container6 = st.empty()
        count = 0
        start_date_time_in_mils = self.date_to_millis(
            self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0)
        six_am_candle_start_time = start_date_time_in_mils + (
                self._one_minute_value_in_ms * 30)
        # This is where one minute converts into 30 minutes for 6AM morning time

        market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
        if market_data is not None:
            high_price = market_data['High']
            low_price = market_data['Low']
            data["Sl.no"] = serial_number
            data["Date"] = dt(
                self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0
            ).strftime("%d/%b/%Y %H:%M:%S.%f %p")
            data["Day"] = dt(
                self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min, 0
            ).strftime("%a")
            data["Trade Type"] = "Long"
            data["IB_H"] = str(high_price)
            data["IB_L"] = str(low_price)
            data["IB%"] = str(((float(high_price) - float(low_price)) / float(low_price)) * 100)

            while (time.time() - start_time) < duration:
                cur_market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
                if market_data is not None:
                    count += 1
                    print(f"Checking for long trade, count {count}")
                    message_container1.caption(
                        f'Checking for short trade at :green[{self.millis_to_date(start_date_time_in_mils)}], '
                        f'Check count: :blue[{count}]'
                    )
                    oi = self.get_open_interest(start_date_time_in_mils)
                    if oi:
                        message_container2.caption(f'Open Interest: :green[{oi}]')
                    message_container3.dataframe(pd.DataFrame([cur_market_data]), hide_index=True)

                    if cur_market_data['Close'] > low_price > cur_market_data['Low']:
                        print("Condition for a Long Trade Have been Found Executing Long Trade - Entry Price: ",
                              cur_market_data["Close"], "Executed at Time ",
                              (dt.fromtimestamp(market_data["Start Time"] / 1000)))
                        message_container4.caption(
                            ":green[Condition for a Long Trade Have been Found Executing Long Trade - Entry Price: ]",
                            cur_market_data['Close'], "Executed at Time ",
                            (dt.fromtimestamp(market_data['Start Time'] / 1000)))
                        self.execute_long_trade(cur_market_data['Close'])
                        logging.info('Long trade executed')
                        data["Entry Price"] = str(cur_market_data['Close'])
                        data["Entry Time"] = str(dt.fromtimestamp(six_am_candle_start_time / 1000))
                        break
                    six_am_candle_start_time += self._one_minute_value_in_ms

                    if six_am_candle_start_time > (start_date_time_in_mils + self._one_day_value_in_ms):
                        print("Long Trade Setup Never occurred, Setup will continue checking the next day")
                        message_container4.caption(
                            ":red[Long Trade Setup Never occurred, Setup will continue checking the next day]"
                        )
                        logging.info('Long trade not executed')

                        data["Entry Price"] = None
                        data["Entry Time"] = None
                        data["SL Price"] = None
                        data["SL Time"] = None
                        data["TP Price"] = None
                        data["TP Time"] = None
                        data["Total % Gain"] = None
                        data["Win-Loss_NoTrade"] = None
                        break
                    message_container5.caption(
                        f'Countdown timer :blue[{np.round((duration - (time.time() - start_time)) / 60, 2)} min]')
                    message_container6.caption(dt.now().strftime("%d/%b/%Y %H:%M:%S.%f %p"))
                    serial_number += 1
                    time.sleep(sleep_time)

    def execute_short_trade(self, entry_price) -> None:
        """
        Win situation:-
        While current low price less than (entry price - entry price * take profit percentage)

        Loss situation:-
        While current high price greater than (entry price + entry price * stop loss percentage)

        No trade situation:-
        While candel_start_date_time_in_ms is greater than (market data start time - one min value * 30) + one day value
        if current close price less than entry price it is win else it is loss
        """
        global data
        message_container1 = st.empty()
        message_container2 = st.empty()
        message_container3 = st.empty()
        start_date_time_in_mils = self.date_to_millis(
            self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min
        )
        while True:
            market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
            if market_data is not None:
                if market_data['Low'] < (float(entry_price) - (float(entry_price) * self.tp_percent)):
                    print("Winning Short Trade Day at " + str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    message_container1.info(
                        "Winning Short Trade Day at " + str((dt.fromtimestamp(start_date_time_in_mils / 1000)))
                    )

                    data["TP Price"] = str(float(entry_price) + (float(entry_price) * self.tp_percent))
                    data["TP Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                    data["SL Price"] = str(float(entry_price) - (float(entry_price) * self.sl_percent))
                    data["SL Time"] = None
                    data["Win Loss No Trade"] = 1
                    data["Total % Gain"] = str((((market_data['Low'] - entry_price) / entry_price) * 100) * 10)
                    break
                if market_data['High'] > (
                        float(entry_price) + (float(entry_price) * self.sl_percent)):
                    print("Loosing  Short Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    message_container2.info(
                        "Loosing  Short Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000)))
                    )

                    data["TP Price"] = str(float(entry_price) + (float(entry_price) * self.tp_percent))
                    data["TP Time"] = None
                    data["SL Price"] = str(market_data['Close'])
                    data["SL Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                    data["Win Loss No Trade"] = 0
                    data["Total % Gain"] = str((((entry_price - market_data['High']) / entry_price) * 100) * 10)
                    break

                candel_start_date_time_in_ms = start_date_time_in_mils + (self._one_minute_value_in_ms * self.interval)
                if candel_start_date_time_in_ms > (
                        (market_data['Start Time'] - (self._one_minute_value_in_ms * 30)) + self._one_day_value_in_ms):
                    print("Trade Never Reached TP and Next day has has arrived, Closing at: " +
                          str(market_data['Close']))
                    message_container3.info("Trade Never Reached TP and Next day has has arrived, Closing at: " +
                            str(market_data['Close']), )

                    if market_data['Close'] < entry_price:
                        data["TP Price"] = str(market_data['Close'])
                        data["TP Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                        data["Win Loss No Trade"] = 1
                    else:
                        data["SL Price"] = str((float(entry_price) + (float(entry_price) * self.sl_percent)))
                        data["SL Time"] = str(dt.fromtimestamp(candel_start_date_time_in_ms / 1000))
                        data["Win Loss No Trade"] = 0
                    break

    def execute_long_trade(self, entry_price) -> None:
        """
        Win situation:-
        While current high greater than (entry price - entry price * take profit percentage)

        Loss situation:-
        While current low price less than (entry price + entry price * stop loss percentage)

        No trade situation:-
        while candel_start_date_time_in_ms greater than (market data start time - one min value * 30) + one day value
        if current close price less than entry price it is win else it is loss
        """
        global data
        message_container1 = st.empty()
        message_container2 = st.empty()
        message_container3 = st.empty()
        start_date_time_in_mils = self.date_to_millis(
            self.start_year, self.start_month, self.start_day, self.start_hour, self.start_min
        )
        while True:
            market_data = self.get_market_data(self.interval, start_date_time_in_mils, start_date_time_in_mils)
            if market_data is not None:
                if market_data['High'] > (float(entry_price) - (float(entry_price) * self.tp_percent)):
                    print("Winning Long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    message_container1.info(
                        "Winning Long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000)))
                    )
                    data["TP Price"] = str(float(entry_price) + (float(entry_price) * self.tp_percent))
                    data["TP Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                    data["SL Price"] = str(float(entry_price) - (float(entry_price) * self.sl_percent))
                    data["SL Time"] = None
                    data["Win Loss No Trade"] = 1
                    data["Total % Gain"] = str((((market_data['Low'] - entry_price) / entry_price) * 100) * 10)
                    break
                if market_data['Low'] < (float(entry_price) + (float(entry_price) * self.sl_percent)):
                    print("Loosing  long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000))))
                    message_container2.info(
                        "Loosing  long Trade Day at ", str((dt.fromtimestamp(start_date_time_in_mils / 1000)))
                    )
                    data["TP Price"] = str(float(entry_price) + (float(entry_price) * self.tp_percent))
                    data["TP Time"] = None
                    data["SL Price"] = str(market_data['Close'])
                    data["SL Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                    data["Win Loss No Trade"] = 0
                    data["Total % Gain"] = str((((entry_price - market_data['High']) / entry_price) * 100) * 10)

                candel_start_date_time_in_ms = start_date_time_in_mils + (self._one_minute_value_in_ms * self.interval)
                if candel_start_date_time_in_ms > (
                        (market_data['Start Time'] - (self._one_minute_value_in_ms * 30)) + self._one_day_value_in_ms):
                    print("Trade Never Reached TP and Next day has has arrived, Closing at: " +
                          str(market_data['Close']))
                    message_container3.info(
                        "Trade Never Reached TP and Next day has has arrived, Closing at: " + str(market_data['Close'])
                    )
                    if market_data['Close'] < entry_price:
                        data["TP Price"] = str(market_data['Close'])
                        data["TP Time"] = str(dt.fromtimestamp(market_data['Start Time'] / 1000))
                        data["Win Loss No Trade"] = 1
                    else:
                        data["SL Price"] = str((float(entry_price) + (float(entry_price) * self.sl_percent)))
                        data["SL Time"] = str(dt.fromtimestamp(candel_start_date_time_in_ms / 1000))
                        data["Win Loss No Trade"] = 0
                    break


class InitiateBybitTrade(CheckAndExecuteTrade):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def check_for_both_long_and_short_trade(self, running_time_in_sec, sleep_time=5) -> pd.DataFrame:
        global data
        self.check_short_trade(running_time_in_sec, sleep_time)
        self.check_for_long_trade(running_time_in_sec, sleep_time)
        return pd.DataFrame([data])

    def bitcoin_trade(self, running_time_in_sec, trade_selection, sleep_time=5) -> pd.DataFrame:
        global data
        if trade_selection == 'Short':
            self.check_short_trade(running_time_in_sec, sleep_time)
        elif trade_selection == 'Long':
            self.check_for_long_trade(running_time_in_sec, sleep_time)
        elif trade_selection == 'Both':
            self.check_for_both_long_and_short_trade(running_time_in_sec, sleep_time)
        return pd.DataFrame([data]).T


def running_time(Hour=0, Min=1, Sec=0):
    return float(Hour * 3600 + Min * 60 + Sec)


if __name__ == '__main__':
    try:
        check_internet()
        initiate_trade = InitiateBybitTrade(start_year=2020, start_month=8, start_day=1, start_hour=5,
                                            start_minute=30, end_year=2024, end_month=4, end_day=29, end_hour=5,
                                            end_min=30)
        # initiate_trade.bitcoin_trade(running_time, 'Short', 5)
        # initiate_trade.bitcoin_trade(running_time, 'Long', 5)
        # initiate_trade.check_for_both_long_and_short_trade(running_time, 5)
        short_trade = threading.Thread(target=initiate_trade.bitcoin_trade, args=(running_time, 'Short', 5))
        long_trade = threading.Thread(target=initiate_trade.bitcoin_trade, args=(running_time, 'Long', 5))
        short_trade.start()
        long_trade.start()
        time.sleep(running_time())
        stop_event.set()
        short_trade.join()
        long_trade.join()
    except Exception as e:
        raise CustomException(e, sys)
