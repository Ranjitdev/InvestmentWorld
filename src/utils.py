from src.logger import logging
from src.exception import CustomException
import os
import sys
import pandas as pd
import numpy as np
from typing import *
from dataclasses import dataclass
from src.Data_ingesion import *
from datetime import datetime as dt
import yfinance as yf
import requests


@dataclass
class UtilityConfigure:
    valid_periods = ['max', '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd']
    valid_intervals = ['1d', '1h', '5d', '1wk', '1mo', '3mo', '1m', '2m', '5m', '15m', '30m', '60m', '90m']


class GetStockDataYfinance:
    def __init__(self, **args):
        self.config = UtilityConfigure
        try:
            self.symbol = args['symbol']
        except:
            raise Exception('Symbol can not be none')
        try:
            self.interval = args['interval']
        except:
            self.interval = None
        try:
            self.period = args['period']
        except:
            self.period = None
        try:
            self.start = args['start']
        except:
            self.start = None
        try:
            self.end = args['end']
        except:
            self.end = None

    def stock_info(self):
        try:
            pass
        except Exception as e:
            CustomException(e, sys)

    def get_data(self) -> pd.DataFrame:
        try:
            ticker_obj = yf.Ticker(self.symbol)
            if self.start is None and self.end is None:
                data = ticker_obj.history(period=self.period, interval=self.interval).drop(
                    ['Dividends', 'Stock Splits'], axis=1).iloc[::-1]
                return data
            if self.end is None and self.start is not None:
                data = ticker_obj.history(period=self.period, interval=self.interval, start=self.start, end=dt.now()
                                          ).drop(['Dividends', 'Stock Splits'], axis=1).iloc[::-1]
                return data
            if self.start is None and self.end is not None:
                data = ticker_obj.history(period=self.period, interval=self.interval).drop(
                    ['Dividends', 'Stock Splits'], axis=1).iloc[::-1]
                return data
            else:
                data = ticker_obj.history(period=self.period, interval=self.interval, start=self.start, end=self.end
                                          ).drop(['Dividends', 'Stock Splits'], axis=1).iloc[::-1]
                return data
        except Exception as e:
            CustomException(e, sys)


def check_internet(url='https://www.google.com', timeout=5):
    """
    Simple check to see if an internet connection seems present
    :param url:
    :param timeout:
    :return:
    """
    try:
        requests.get(url, timeout=timeout)
        logging.info('Connected to internet')
    except Exception as e:
        logging.info(f'Connection error {e}')
        raise CustomException(e, sys)


