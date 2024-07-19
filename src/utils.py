from src.logger import logging
from src.exception import CustomException
import os
import sys
import pandas as pd
import numpy as np
from typing import *
from dataclasses import dataclass
from src.Data_ingesion import *
import requests


@dataclass
class UtilityConfigure:
    pass


def check_internet(url='https://www.google.com', timeout=5) -> None:
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


def make_textdoc(name: str, text: str) -> None:
    """
    :param name:
    :param text:
    :return:
    """
    try:
        file = f'artifacts/{name}.txt'
        with open(file, 'w') as file_obj:
            file_obj.write(text)
    except Exception as e:
        logging.info(f'Connection error {e}')
        raise CustomException(e, sys)


def read_textdoc(name: str) -> str:
    """
    :param name:
    :return:
    """
    try:
        file = f'artifacts/{name}.txt'
        with open(file, 'r') as file_obj:
            return file_obj.read()
    except Exception as e:
        logging.info(f'Connection error {e}')
        raise CustomException(e, sys)




