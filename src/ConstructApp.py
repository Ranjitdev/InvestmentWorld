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
from datetime import timedelta


class InitializeApp:
    def __init__(self):
        self.full_data = DataIngesion().get_data()
        self.sym_data = DataIngesion().get_data(market_cap=False)
        self.market_cap_data = DataIngesion().get_data(symbol=False)
        self.bybit_intervals = [1, 3, 5, 15, 30, 60, 120, 240, 360, 720, 'D', 'M', 'W']

    @staticmethod
    def start_loop():
        st.session_state.loop_running = True

    @staticmethod
    def stop_loop():
        st.session_state.loop_running = False

    def home(self):
        try:
            pass
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')

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
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1d', '5d', '1wk', '1mo', '3mo']
        try:
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
        with st.form('form_1'):
            st.header('Search for Short or Long trade')

            col1, col2, col3 = st.columns(3)
            with col1:
                start_date = st.date_input(
                    'Start Date', value='today', min_value=dt(2000, 1, 1), max_value=dt.now()
                )
                start_hour = st.slider('Start hour', value=5, min_value=0, max_value=23)
                start_min = st.slider('Start min', value=30, min_value=0, max_value=55, step=5)
                start_datetime = dt(start_date.year, start_date.month, start_date.day, start_hour, start_min)
            with col2:
                end_date = st.date_input(
                    'End Date', value='today', min_value=dt(2000, 1, 1), max_value=dt.now()
                )
                end_hour = st.slider('End hour', value=9, min_value=0, max_value=23)
                end_min = st.slider('End min', value=30, min_value=0, max_value=55, step=5)
                end_datetime = dt(end_date.year, end_date.month, end_date.day, end_hour, end_min)
            with col3:
                selection = st.selectbox('Select trade type', ['Both', 'Short', 'Long'])
                interval = st.selectbox('Interval', self.bybit_intervals)

            st.caption(str(dt.now().strftime('%d/%b/%Y %H:%M:%S.%f %p')))
            if st.form_submit_button('Start', on_click=self.start_loop()):
                try:
                    check_internet()
                    if start_datetime < end_datetime:
                        initiate_trade = InitiateBybitTrade(start_datetime, end_datetime, interval)
                        if selection == 'Short':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                            st.dataframe(data)
                        if selection == 'Long':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                            st.dataframe(data)
                        if selection == 'Both':
                            with st.spinner('Wait while checking...'):
                                data = initiate_trade.bitcoin_trade(selection)
                                data.to_csv(DataIngesionConfig.bybit_test_data, index=False)
                            st.dataframe(data)
                    else:
                        st.warning('Check Start date and End date')
                except Exception as e:
                    logging.error(e)
                    st.error(f'⚠ Got Error {e}')
                    raise CustomException(e, sys)

    def file_viewer(self):
        try:
            pass
        except Exception as e:
            st.warning(f'Processing Error: {e}', icon='⚠')




