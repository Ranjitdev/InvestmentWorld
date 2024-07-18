import time
import numpy as np
import pandas as pd
from src.logger import logging
from src.exception import CustomException
import sys
import os
from src.utils import *
from datetime import datetime as dt
from datetime import timedelta
from pybit.unified_trading import HTTP
import streamlit as st
import threading
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')


@dataclass
class YfinanceConfigure:
    valid_periods = ['max', '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd']
    valid_intervals = ['1d', '1h', '5d', '1wk', '1mo', '3mo', '1m', '2m', '5m', '15m', '30m', '60m', '90m']


class YfinanceData:
    def __init__(self, symbol, interval, period, start, end):
        self.config = YfinanceConfigure
        self.symbol = symbol
        self.interval =interval
        self.period = period
        self.start = start
        self.end = end

    def stock_info(self) -> Any:
        try:
            ticker_obj = yf.Ticker(self.symbol)
            if ticker_obj.info is not None:
                return ticker_obj.info
        except Exception as e:
            raise CustomException(e, sys)

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
            raise CustomException(e, sys)