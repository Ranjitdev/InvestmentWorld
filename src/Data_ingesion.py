from src.logger import logging
from src.exception import CustomException
import os
import sys
import pandas as pd
import numpy as np
from typing import *
from dataclasses import dataclass


@dataclass
class DataIngesionConfig:
    data_url = r'https://www.nseindia.com/regulations/listing-compliance/nse-market-capitalisation-all-companies'
    data_path = r'artifacts/data.xlsx'
    notebook_data_path = r'notebook/data.xlsx'


class DataIngesion:
    def __init__(self):
        self.config = DataIngesionConfig
        files = []
        for file in os.listdir('artifacts/'):
            files.append(file)
        if 'data.xlsx' not in files:
            raise Exception('data error')

    def get_data(self, market_cap=True, symbol=True) -> pd.DataFrame:
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
            CustomException(e, sys)



