from src.logger import logging
from src.exception import CustomException
import os
import sys
import pandas as pd
import numpy as np
from typing import *
from dataclasses import dataclass
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials


@dataclass
class DataIngesionConfig:
    data_url = r'https://www.nseindia.com/regulations/listing-compliance/nse-market-capitalisation-all-companies'
    data_path = r'artifacts/tickers.xlsx'
    notebook_data_path = r'notebook/tickers.xlsx'
    bybit_test_data = r'artifacts/bybit_data.csv'
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'artifacts/creditcarddefault-396210-13114272d388.json', scope)
    client = gspread.authorize(creds)


class DataIngesion:
    def __init__(self):
        self.config = DataIngesionConfig
        files = []
        for file in os.listdir('artifacts/'):
            files.append(file)
        if 'tickers.xlsx' not in files:
            raise Exception('data error')

    def get_tickers_data(self, market_cap=True, symbol=True) -> pd.DataFrame:
        try:
            data = pd.read_excel(self.config.data_path, index_col=None)
            if not market_cap and not symbol:
                data.drop(['Sr. No.', 'Market capitalization as on March 28, 2024\n(In lakhs)', 'Symbol'],
                          axis=1, inplace=True)
                data.columns = ['Name']
            elif not market_cap:
                data.drop(['Sr. No.', 'Market capitalization as on March 28, 2024\n(In lakhs)'], axis=1, inplace=True)
                data.columns = ['Symbol', 'Name']
            elif not symbol:
                data.drop(['Sr. No.', 'Symbol'], axis=1, inplace=True)
                data.columns = ['Name', 'Market Cap (in Lakhs)']
            else:
                data.drop('Sr. No.', axis=1, inplace=True)
                data.columns = ['Symbol', 'Name', 'Market Cap (in Lakhs)']
            return data
        except Exception as e:
            logging.error(e)
            raise CustomException(e, sys)

    def get_bybit_data(self) -> pd.DataFrame or None:
        try:
            data = pd.read_csv(self.config.bybit_test_data, index_col=False)
            return data
        except:
            return None

    def update_bybit_data(self, file: pd.DataFrame) -> None:
        try:
            data = pd.read_csv(self.config.bybit_test_data, index_col=False)
            new_data = pd.concat([data, file], ignore_index=True)
            new_data.iloc[::-1].reset_index(drop=True).to_csv(self.config.bybit_test_data, index=False)
        except Exception as e:
            raise CustomException(e, sys)

    def update_gsheet(self, data):
        try:
            spreadsheet = DataIngesionConfig.client.open('bybit_data')
            worksheet = spreadsheet.get_worksheet(0)
            previous_data = worksheet.get_all_records()
            previous_data = pd.DataFrame(previous_data)
            print(previous_data)
            new_data = pd.concat([data, previous_data], ignore_index=True)
            new_data = new_data.iloc[::-1].reset_index(drop=True)
            worksheet.clear()
            set_with_dataframe(worksheet, new_data)
        except Exception as e:
            raise CustomException(e, sys)

    def update_mysql_server(self, db: dict, data: pd.DataFrame) -> None:
        try:
            pass
        except Exception as e:
            raise CustomException(e, sys)





