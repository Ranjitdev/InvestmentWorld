import datetime
import time
from pybit.unified_trading import HTTP
import pandas as pd
import requests
import json

from colorama import init, Fore, Back, Style

init()

# Data to be sent
data = {
    "Sl.no": "1",
    "Date": "2024-04-28",
    "Day": "Sunday",
    "Trade Type": "Long",
    "IB_H": "100",
    "IB_L": "90",
    "IB%": "10",
    "Entry Price": "95",
    "Entry Time": "10:00",
    "SL Price": "92",
    "SL Time": "10:15",
    "TP Price": "105",
    "TP Time": "105",
    "Total % Gain": "5",
    "Win-Loss_NoTrade": "Y"
}

#url = "https://script.google.com/macros/s/AKfycbxytnKW16XGGdAAK3e2_DY1vVdZVvZCFZlulQyM9zahtG9TDD-Mc0LsXcMOluEGqnf4/exec"
url = 'your google sheet link'

session = HTTP(
    testnet=False,
    api_key="QJMjsUMadgwSbfsrayQQ",
    api_secret="3tydxkjlghCHbBCcVtyjlcaWzLG4zRfouPKgztsajfbjjiLTjlkEv",
)

# start_day_value_in_mils = 1634688000000 # This is 20th OCT 2021 5:30 IST
# end_29min_value_in_mils = 1634689740000 # This is 20th OCT 2021 5:59 IST

start_date_time_in_mils = 1596240000000  # 1711929600000  # This is 20th OCT 2021 5:30 IST
end_date_time_in_mils = 1714348800000

ib_high = 0  # Initial Balance
ib_low = 0

one_minute_value_in_ms = 60000
one_day_value_in_ms = 86400000
tp_percent = 0.3 / 100  # 0.25% TP Take Profit
sl_percent = 1.5 / 100  # 1.5% SL Stop Loss

trade_setup = 0  # 0 - Only Short 1 - only long 2 - both long and short

# Kline interval. 1,3,5,15,30,60,120,240,360,720,D,M,W
check_for_close_in_TF = 1  # This is to change i want to ckek for 1m close 2 min close 3 min cloe or other

serial_number = 1


def is_internet_available():
    """Simple check to see if an internet connection seems present"""
    try:
        requests.get('https://www.google.com', timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False

def get_ib_values(start_time_in_ms):
    max_retries = 20  # Maximum number of retries
    retry_delay = 5  # Seconds to wait between retries

    for attempt in range(max_retries):
        if is_internet_available():
            try:
                open_interest_data = session.get_open_interest(
                    category="inverse",
                    symbol="BTCUSD",
                    intervalTime="30min",
                    startTime=start_time_in_ms,
                    endTime=start_time_in_ms + 1740000,
                )
                OI = open_interest_data['result']['list'][0]['openInterest']

                print(OI)

            except IndexError:
                print("index error has occured")


            try:
                data = session.get_kline(
                    category="linear",
                    symbol="BTCUSDT",
                    interval=30,
                    start=start_time_in_ms,
                    end=start_time_in_ms + 1740000
                )

                market_data_list = data['result']['list']

                for data_point in market_data_list:
                    high_price = data_point[2]
                    low_price = data_point[3]
                    volume = data_point[5]
                    turnover = data_point[6]

                    ib_low = float(low_price)
                    ib_high = float(high_price)

                    print("IB High of the day is: ", ib_high)
                    print("IB Low of the day is: ", ib_low)
                    print("Volume: ",volume)
                    print("Turnover", turnover)
                    print("")

                    return ib_high, ib_low,

            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)  # Wait before retrying
        else:
            print("No internet connection. Retrying...")
            time.sleep(retry_delay)

    # If all retries fail:
    print("Failed to get data after multiple retries.")
    return None, None  # Or raise an exception if you prefer


def get_kline_data(interval, start_value, end_value):
    max_retries = 50
    retry_delay = 5

    for attempt in range(max_retries):
        if is_internet_available():
            try:
                data = session.get_kline(
                    category="linear",
                    symbol="BTCUSDT",
                    interval=interval,
                    start=start_value,
                    end=end_value
                )

                kline_data_list = data['result']['list']
                df_list = []
                for item in kline_data_list:
                    df_list.append({
                        'startTime': pd.to_datetime(int(item[0]), unit='ms'),
                        'openPrice': float(item[1]),
                        'highPrice': float(item[2]),
                        'lowPrice': float(item[3]),
                        'closePrice': float(item[4]),
                        'volume': float(item[5]),
                        'turnover': float(item[6]),
                    })

                # Assuming you want the data from the last item
                last_item = kline_data_list[-1]
                startTime = pd.to_datetime(int(last_item[0]), unit='ms')
                openPrice = float(last_item[1])
                highPrice = float(last_item[2])
                lowPrice = float(last_item[3])
                closePrice = float(last_item[4])

                return startTime, openPrice, highPrice, lowPrice, closePrice

            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
        else:
            print("No internet connection. Retrying...")
            time.sleep(retry_delay)

    # If all retries fail:
    print("Failed to get data after multiple retries.")
    return None, None, None, None, None  # Or raise an exception


def app_init(start_date_time, end_date_time):
    while start_date_time <= end_date_time:
        IB_H, IB_L = get_ib_values(start_date_time)

        # check_for_short_trade_only
        if trade_setup == 0:
            print("Looking for Short Trades Only")
            check_for_short_trade(IB_H, IB_L, start_date_time)

        # check_for_long_trade_only
        if trade_setup == 1:
            print("Looking for Long Trade Only")
            check_for_long_trade(IB_H, IB_L, start_date_time)

        # check_for_short_and_long_trade
        if trade_setup == 2:
            print("Looking for both long and short trades")
            check_for_both_long_and_short_trade(IB_H, IB_L, start_date_time)

        # response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        # print(response.text)

        start_date_time += one_day_value_in_ms


def check_for_short_trade(IB_H, IB_L, start_date_time):
    global serial_number

    data["Sl.no"] = serial_number
    data["Date"] = str((datetime.datetime.fromtimestamp(start_date_time / 1000)))
    date_string = str((datetime.datetime.fromtimestamp(start_date_time / 1000)))
    data["Day"] = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime("%A")
    data["Trade Type"] = "Short"
    data["IB_H"] = str(IB_H)
    data["IB_L"] = str(IB_L)
    data["IB%"] = str(((float(IB_H) - float(IB_L)) / float(IB_L)) * 100)

    print("Checking for a Short Trade Now on Date and Time: ",
          (datetime.datetime.fromtimestamp(start_date_time / 1000)))

    six_am_candle_start_time = start_date_time + (
                one_minute_value_in_ms * 30)  # This is where one munite convertes into 30 munites for 6AM morning time
    six_am_candle_end_time = start_date_time + (
                one_minute_value_in_ms * 30)  # This is where one munite convertes into 30 munites for 6AM morning time
    flag = 0
    while True:
        startTime, openPrice, one_minute_high_price, one_minute_low_price, one_minute_close_price = get_kline_data(
            check_for_close_in_TF, six_am_candle_start_time, six_am_candle_end_time)
        print("openPrice ", openPrice)
        print("HighPrice ", one_minute_high_price)
        print("LowPrice ", one_minute_low_price)
        print("Date and Time: ",  datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
        print("###############")
        print("")

        if one_minute_high_price > IB_H:
            flag = 1  # This means the Price went above IB
        if (one_minute_close_price < IB_H) and flag == 1:
            print("Condition for a short Trade Have been Found Executing Short Trade - Entry Price: ",
                  one_minute_close_price, "Executed at Time ",
                  (datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000)))
            flag = 0
            execute_short_trade(one_minute_close_price, tp_percent, sl_percent, six_am_candle_start_time,
                                six_am_candle_end_time)
            data["Entry Price"] = str(one_minute_close_price)
            data["Entry Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))

            break

        six_am_candle_start_time += one_minute_value_in_ms
        six_am_candle_end_time += one_minute_value_in_ms

        if six_am_candle_end_time > (start_date_time + one_day_value_in_ms):
            print("Short Trade Setup Never occurred")
            print("Setup will continue checking the next day")
            data["Entry Price"] = "-"
            data["Entry Time"] = "-"
            data["SL Price"] = "-"
            data["SL Time"] = "-"
            data["TP Price"] = "-"
            data["TP Time"] = "-"
            data["Total % Gain"] = "-"
            data["Win-Loss_NoTrade"] = "-"
            break
    response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    print(response.text)
    serial_number += 1


def execute_short_trade(entry_price, tp_percent, sl_percent, six_am_candle_start_time, six_am_candle_end_time):
    candel_start_date_time_in_ms = six_am_candle_start_time
    candel_end_date_time_in_ms = six_am_candle_end_time

    while True:
        startTime, openPrice, one_minute_high_price, one_minute_low_price, one_minute_close_price = get_kline_data(
            check_for_close_in_TF,
            candel_start_date_time_in_ms,
            candel_end_date_time_in_ms)

        if one_minute_low_price < (float(entry_price) - (float(entry_price) * tp_percent)):  # calculated TP Price:
            print(Fore.GREEN + "Winning Short Trade Day at ",
                  str((datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))) + Style.RESET_ALL)
            data["TP Price"] = str(float(entry_price) + (float(entry_price) * tp_percent))
            data["TP Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
            data["SL Price"] = str(float(entry_price) - (float(entry_price) * sl_percent))
            data["SL Time"] = "-"
            data["Win-Loss_NoTrade"] = "1"
            data["Total % Gain"] = str((-((one_minute_low_price - entry_price) / entry_price) * 100) * 10)
            break
        if one_minute_high_price > (float(entry_price) + (float(entry_price) * sl_percent)):  # calculated SL Price
            print(Fore.RED + "Loosing  Short Trade Day at ",
                  str((datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))) + Style.RESET_ALL)
            data["TP Price"] = str(float(entry_price) + (float(entry_price) * tp_percent))
            data["TP Time"] = "-"
            data["SL Price"] = str(one_minute_close_price)
            data["SL Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
            data["Win-Loss_NoTrade"] = "0"
            data["Total % Gain"] = str((((entry_price - one_minute_high_price) / entry_price) * 100) * 10)
            break

        candel_start_date_time_in_ms = candel_start_date_time_in_ms + (one_minute_value_in_ms * check_for_close_in_TF)
        candel_end_date_time_in_ms = candel_end_date_time_in_ms + (one_minute_value_in_ms * check_for_close_in_TF)

        if candel_end_date_time_in_ms > (
                (six_am_candle_start_time - (one_minute_value_in_ms * 30)) + one_day_value_in_ms):
            print("Trade Never Reached TP and Next day has has arrived, Closing at: ", one_minute_close_price)
            if one_minute_close_price < entry_price:
                data["TP Price"] = str(one_minute_close_price)
                data["TP Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
                data["Win-Loss_NoTrade"] = "1"
            else:
                data["SL Price"] = str((float(entry_price) + (float(entry_price) * sl_percent)))
                data["SL Time"] = str(datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))
                data["Win-Loss_NoTrade"] = "0"
            break


def check_for_long_trade(IB_H, IB_L, start_date_time):
    global serial_number

    data["Sl.no"] = serial_number
    data["Date"] = str((datetime.datetime.fromtimestamp(start_date_time / 1000)))
    date_string = str((datetime.datetime.fromtimestamp(start_date_time / 1000)))
    data["Day"] = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime("%A")
    data["Trade Type"] = "Long"
    data["IB_H"] = str(IB_H)
    data["IB_L"] = str(IB_L)
    data["IB%"] = str(((IB_H - IB_L) / IB_L) * 100)

    print("Checking for a Long Trade Now on Date and Time: ", (datetime.datetime.fromtimestamp(start_date_time / 1000)))

    six_am_candle_start_time = start_date_time + (
            one_minute_value_in_ms * 30)  # This is where one munite convertes into 30 munites for 6AM morning time
    six_am_candle_end_time = start_date_time + (
            one_minute_value_in_ms * 30)  # This is where one munite convertes into 30 munites for 6AM morning time
    flag = 0
    while True:
        startTime, openPrice, one_minute_high_price, one_minute_low_price, one_minute_close_price = get_kline_data(
            check_for_close_in_TF, six_am_candle_start_time, six_am_candle_end_time)
        # print("openPrice ", openPrice)
        # print("HighPrice ", one_minute_high_price)
        # print("LowPrice ", one_minute_low_price)
        # print("Date and Time: ", datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
        # print("###############")
        # print("")

        if one_minute_low_price < IB_L:
            flag = 1  # This means the Price went above IB
        if (one_minute_close_price > IB_L) and flag == 1:
            print("Condition for a Long Trade Have been Found Executing Long Trade - Entry Price: ",
                  one_minute_close_price, "Executed at Time ",
                  (datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000)))
            flag = 0
            execute_long_trade(one_minute_close_price, tp_percent, sl_percent, six_am_candle_start_time,
                               six_am_candle_end_time)
            data["Entry Price"] = str(one_minute_close_price)
            data["Entry Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
            break

        six_am_candle_start_time += one_minute_value_in_ms
        six_am_candle_end_time += one_minute_value_in_ms

        if six_am_candle_end_time > (start_date_time + one_day_value_in_ms):
            print("Long Trade Setup Never occurred")
            print("Setup will continue checking the next day")

            data["Entry Price"] = "-"
            data["Entry Time"] = "-"
            data["SL Price"] = "-"
            data["SL Time"] = "-"
            data["TP Price"] = "-"
            data["TP Time"] = "-"
            data["Total % Gain"] = "-"
            data["Win-Loss_NoTrade"] = "-"
            break
    response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    print(response.text)
    serial_number += 1


def execute_long_trade(entry_price, tp_percent, sl_percent, six_am_candle_start_time, six_am_candle_end_time):
    candel_start_date_time_in_ms = six_am_candle_start_time
    candel_end_date_time_in_ms = six_am_candle_end_time

    while True:
        startTime, openPrice, one_minute_high_price, one_minute_low_price, one_minute_close_price = get_kline_data(
            check_for_close_in_TF,
            candel_start_date_time_in_ms,
            candel_end_date_time_in_ms)

        if one_minute_high_price > (float(entry_price) + (float(entry_price) * tp_percent)):
            # calculated TP Price:
            print(Fore.GREEN + "Winning Long Trade Day at ",
                  str((datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))) + Style.RESET_ALL)
            data["TP Price"] = str(float(entry_price) + (float(entry_price) * tp_percent))
            data["TP Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
            data["SL Price"] = str(float(entry_price) - (float(entry_price) * sl_percent))
            data["SL Time"] = "-"
            data["Win-Loss_NoTrade"] = "1"
            data["Total % Gain"] = str((((one_minute_high_price - entry_price) / entry_price) * 100) * 10)
            break
        if one_minute_low_price < (float(entry_price) - (float(entry_price) * sl_percent)):  # calculated SL Price
            print(Fore.RED + "Loosing Long Trade Day at ",
                  str((datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))) + Style.RESET_ALL)
            data["TP Price"] = str(float(entry_price) + (float(entry_price) * tp_percent))
            data["TP Time"] = "-"
            data["SL Price"] = str(one_minute_close_price)
            data["SL Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
            data["Win-Loss_NoTrade"] = "0"
            data["Total % Gain"] = str((-((entry_price - one_minute_low_price) / entry_price) * 100) * 10)
            break

        candel_start_date_time_in_ms = candel_start_date_time_in_ms + (one_minute_value_in_ms * check_for_close_in_TF)
        candel_end_date_time_in_ms = candel_end_date_time_in_ms + (one_minute_value_in_ms * check_for_close_in_TF)

        if candel_end_date_time_in_ms > (
                (six_am_candle_start_time - (one_minute_value_in_ms * 30)) + one_day_value_in_ms):
            print("Trade Never Reached TP and Next day has has arrived, Closing at: ", one_minute_close_price)
            if one_minute_close_price < entry_price:
                data["TP Price"] = str(one_minute_close_price)
                data["TP Time"] = str(datetime.datetime.fromtimestamp(six_am_candle_start_time / 1000))
                data["Win-Loss_NoTrade"] = "1"
            else:
                data["SL Price"] = str((float(entry_price) + (float(entry_price) * sl_percent)))
                data["SL Time"] = str(datetime.datetime.fromtimestamp(candel_end_date_time_in_ms / 1000))
                data["Win-Loss_NoTrade"] = "0"
            break


def check_for_both_long_and_short_trade(IB_H, IB_L, start_date_time):
    check_for_long_trade(IB_H, IB_L, start_date_time)
    check_for_short_trade(IB_H, IB_L, start_date_time)


def send_data_to_google_sheet():
    return 0


def main():
    # check_every_1m_candel_after_the_IB_ie_after_6AM_IST_and_onwards()
    # check_for_a_long_or_short_trade_setup()
    # get_ib_values(start_date_time_in_mils)

    #app_init(start_date_time_in_mils, end_date_time_in_mils)
    value = start_date_time_in_mils
    for i in range(1, 101):
        print(i)
        get_ib_values(value)
        value += one_day_value_in_ms
        time.sleep(1)





if __name__ == "__main__":
    main()

# def find_the_ib():
#     print("test")
#
