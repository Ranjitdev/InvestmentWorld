from src.logger import logging
from src.exception import CustomException
import os
import sys
import pandas as pd
import numpy as np
from typing import *
from dataclasses import dataclass
from src.Data_ingesion import *
from src.Bybit_manager import *
import streamlit as st
from streamlit.errors import NoSessionContext
from streamlit.runtime.scriptrunner.script_run_context import (SCRIPT_RUN_CONTEXT_ATTR_NAME, get_script_run_ctx)
from streamlit.runtime.scriptrunner import add_script_run_ctx
from src.utils import *
import time


class InitializeApp:
    def __init__(self):
        self.full_data = DataIngesion().get_data()
        self.sym_data = DataIngesion().get_data(market_cap=False)
        self.market_cap_data = DataIngesion().get_data(symbol=False)

    def home(self):
        try:
            pass
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')

    @staticmethod
    def refresh_data():
        pass

    def today(self):
        try:
            data = self.sym_data
            col1, col2 = st.columns(2)
            with col1:
                name_selection = st.selectbox('Stock', ['Select'] + list(data['Name']))
            with col2:
                interval = st.selectbox('Interval', ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'])
            if name_selection != 'Select':
                ticker_sym = str(data[data['Name'] == name_selection]['Symbol'].item()) + '.NS'
                while True:
                    data = GetStockDataYfinance(symbol=ticker_sym, period='1d', interval=interval).get_data()
                    placeholder = st.empty()
                    with placeholder.container():
                        open_col, high_col, low_col, close_col, vol_col = st.columns(5)
                        with open_col:
                            st.caption('Open')
                            st.subheader(np.round(data.iloc[0, 0], 2))
                        with high_col:
                            st.caption('High')
                            st.subheader(np.round(data.iloc[0, 1], 2))
                        with low_col:
                            st.caption('Low')
                            st.subheader(np.round(data.iloc[0, 2], 2))
                        with close_col:
                            st.caption('Close')
                            st.subheader(np.round(data.iloc[0, 3], 2))
                        with vol_col:
                            st.caption('Volume')
                            st.subheader(np.round(data.iloc[0, 4], 2))
                        st.dataframe(data)
                        time.sleep(5)
                    placeholder.empty()

            else:
                pass
        except Exception as e:
            logging.error(f'Processing Error: {e}')
            st.warning(f'Processing Error: {e}', icon='⚠')

    def historical(self):
        try:
            data = self.sym_data
            col1, col2, col3 = st.columns(3)
            with col1:
                name_selection = st.selectbox('Company', ['Select'] + list(data['Name']))
            with col2:
                interval = st.selectbox('Interval', UtilityConfigure.valid_intervals)
            with col3:
                period = st.selectbox('Period', UtilityConfigure.valid_periods)
            col4, col5 = st.columns(2)
            with col4:
                start = st.date_input('Start Date', None, min_value=dt(1970, 1, 1), max_value=dt.now())
            with col5:
                end = st.date_input('End Date', None, min_value=dt(2000, 1, 1), max_value=dt.now())
            if name_selection != 'Select':
                ticker_sym = str(data[data['Name'] == name_selection]['Symbol'].item()) + '.NS'
                data = GetStockDataYfinance(symbol=ticker_sym, interval=interval, period=period, start=start, end=end
                                            ).get_data()
                st.dataframe(data)
        except Exception as e:
            logging.error(f'Processing Error: {e}')
            st.warning(f'Processing Error: {e}', icon='⚠')

    def bitcoin(self):
        try:
            valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1d', '5d', '1wk', '1mo', '3mo']
            col1, col2 = st.columns(2)
            with col1:
                period = st.selectbox('Period', valid_periods)
            with col2:
                interval = st.selectbox('Interval', valid_intervals)

            while True:
                data = GetStockDataYfinance(symbol='BTC-USD', interval=interval, period=period).get_data()
                placeholder = st.empty()
                with placeholder.container():
                    open_col, high_col, low_col, close_col, vol_col = st.columns(5)
                    with open_col:
                        st.caption('Open')
                        st.subheader(np.round(data.iloc[0, 0], 2))
                    with high_col:
                        st.caption('High')
                        st.subheader(np.round(data.iloc[0, 1], 2))
                    with low_col:
                        st.caption('Low')
                        st.subheader(np.round(data.iloc[0, 2], 2))
                    with close_col:
                        st.caption('Close')
                        st.subheader(np.round(data.iloc[0, 3], 2))
                    with vol_col:
                        st.caption('Volume')
                        st.subheader(np.round(data.iloc[0, 4], 2))

                    st.dataframe(data)
                    time.sleep(5)

                placeholder.empty()
        except Exception as e:
            logging.error(f'Processing Error: {e}')
            st.warning(f'Processing Error: {e}', icon='⚠')

    def bybit(self):
        try:
            check_internet()
        except:
            st.warning('⚠ Not connected to internet, Please connect to 🌐internet and 🔄refresh')
        with st.form('form1'):
            st.header('Search for Short trade or Long trade')
            st.text('Run time of application')
            col1, col2, col3 = st.columns(3)
            with col1:
                Hour = int(st.selectbox('Hour', [i for i in range(120)]))
            with col2:
                Min = int(st.number_input('Minute', min_value=1, max_value=60, step=1, value=5))
            with col3:
                Sec = int(st.number_input('Second', min_value=0, max_value=60, step=1, value=0))
            col4, col5 = st.columns(2)
            with col4:
                selection = st.selectbox('Select trade type', ['Short', 'Long', 'Both'])
            with col5:
                interval = st.number_input('Interval between two search', min_value=5, max_value=300, value=10, step=5)
            initiate_trade = InitiateBybitTrade(start_year=2020, start_month=8, start_day=1, start_hour=5,
                                                start_minute=30, end_year=2024, end_month=4, end_day=29, end_hour=5,
                                                end_min=30)
            if st.form_submit_button('Start'):
                try:
                    check_internet()
                    if selection == 'Short':
                        data = initiate_trade.bitcoin_trade(running_time(Hour, Min, Sec), selection, interval)
                        st.dataframe(data)
                    if selection == 'Long':
                        data = initiate_trade.bitcoin_trade(running_time(Hour, Min, Sec), selection, interval)
                        st.dataframe(data)
                    if selection == 'Both':
                        data = initiate_trade.bitcoin_trade(running_time(Hour, Min, Sec), selection, interval)
                        st.dataframe(data)
                except Exception as e:
                    st.error(f'⚠ Got Error {e}')

    def file_viewer(self):
        try:
            pass
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')




