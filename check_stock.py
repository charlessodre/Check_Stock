# Create by: Charles Sodré (https://github.com/charlessodre/Check_Stock)
# Date: 08/2019
# Based in course of Saulo Catharino: https://github.com/saulocatharino/machine_learning_for_traders
#

# Library Import
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import logging
import helper
# https://github.com/rahiel/telegram-send
import telegram_send

logging.basicConfig(filename=helper.path_join('log', 'application_log.log'), level=logging.ERROR)

CONFIG_FILE_PATH = helper.path_join('config', 'config.txt')
BASE_PATH = 'base'
SOURCE_URL = None  # 'https://br.investing.com/equities/usiminas-pna'
STOCK_FILE = None

# [0 (Sunday), 1 (Monday) ... 6 (Saturday)].
WEEKDAYS_EXECUTION = None  # [1, 2, 3, 4, 5]
BEGIN_HOUR_EXECUTION = None  # 9
END_HOUR_EXECUTION = None  # 17

BOLLINGER_CALCULATION_WINDOW = None  # 40
BOLLINGER_STANDARD_DEVIATION = None  # 2

X_AXIS_VIEW_LIMIT = None  # 30
TARGET_PRICE_MINIMUM = None  # 7.3
TARGET_PRICE_MAXIMUM = None  # 7.6

SHOW_MAIN_CHART = True
SHOW_BOLLINGER_BANDS_CHART = True
SHOW_TARGET_PRICES_CHART = True
SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS = True
SEND_NOTIFICATION_CROSS_TARGET_PRICES = False
INTERVAL_BETEWEEN_RUNS = 20
READ_LAST_LINES_STOCK_FILE = 50

NUM_ERRORS_MAIN = 0

BOLLINGER_SELL = []
BOLLINGER_BUY = []
BOLLINGER_INDEX_SELL = []
BOLLINGER_INDEX_BUY = []
BOLLINGER_SIGNAL = []

mpl.rcParams['toolbar'] = 'None'
fig = plt.figure(figsize=(16, 8))
# fig.canvas.set_window_title('Acompanhamento Valor Ação')
# fig.suptitle('USIM5')
axes = fig.gca()


def get_configs(config_file_path):
    settings = {}

    configs = helper.read_file(config_file_path, 'r')
    for config in configs:
        if len(config.strip()) > 10:
            items = config.split('=')
            settings[items[0]] = items[1]

    return settings


def get_last_stock_price_ADVN(source_url):
    # SOURCE_URL = 'https://br.investing.com/equities/usiminas-pna'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    con = requests.get(source_url, headers=headers)

    # Status 200 Ok.
    # https://www.w3.org/Protocols/HTTP/1.1/draft-ietf-http-v11-spec-01#Status-Codes
    # con.status_code

    soup = BeautifulSoup(con.content, "html.parser")

    main_div = soup.find('div', {'id': 'quotes_summary_current_data'})

    sotck_price_tag = main_div.find('span', {'id': 'last_last'})

    stock_price = sotck_price_tag.text

    stock_price = stock_price.replace('.', '').replace(',', '.')

    stock_price = float(stock_price)

    return stock_price


def save_stock_price(stock_file, price):
    stock_price_list = []

    if helper.file_exists(stock_file):
        stock_price_list = helper.read_file(stock_file)

    stock_entry = '{};{};{}'.format(price, helper.get_current_date_str(), helper.get_current_hour())
    stock_price_list.append(stock_entry)

    helper.save_list_to_file(stock_file, stock_price_list, mode='w')


def check_execution_hour(begin, end):
    current_hour = int(helper.get_hour_str())

    return begin <= current_hour <= end


def check_execution_day(weekdays):
    current_num_day = helper.get_current_number_weekday()

    return current_num_day in weekdays


def plot_main_chart(ax, stock_list, time, window):
    ax.clear()

    ax.set_xlim(len(stock_list) - window * 2, len(stock_list) + 5)

    # ax.set(xlabel='time (s)', ylabel='USIM5', title='Acompanhamento value Ação')

    x_axis_current = time[-1:].max()
    y_axis_current = stock_list[-1:].max()
    y_axis_last = stock_list[-2:-1].max()

    if y_axis_current >= y_axis_last:
        ax.text(x_axis_current, y_axis_current, y_axis_current, fontsize=8, bbox=dict(facecolor='green', alpha=0.3))
    else:
        ax.text(x_axis_current, y_axis_current, y_axis_current, fontsize=8, bbox=dict(facecolor='red', alpha=0.3))

    ax.plot(time, stock_list, label='Stock Price')

    plt.yticks(fontsize=8)
    plt.xticks(fontsize=8, rotation=45)


def plot_bollinger_bands_chart(ax, upper_band, lower_band):
    ax.plot(upper_band, '--', color="green", alpha=.2, label='BB Up')
    ax.plot(lower_band, '--', color="red", alpha=.2, label='BB Down')


def plot_line_chart(ax, list_size, value, color_name, marker="*", legend=None, alpha=0.5):
    lim = np.empty(list_size)
    lim.fill(value)
    ax.plot(lim, marker, color=color_name, alpha=alpha, label=legend)


def calc_bollinger_bands(stock_list, window_avg_calc, deviation):
    bb_lower = None
    bb_upper = None

    if len(stock_list) > window_avg_calc:
        media = stock_list.rolling(window=window_avg_calc).mean()
        rolling_std = stock_list.rolling(window=window_avg_calc).std()
        bb_upper = media + (rolling_std * deviation)
        bb_lower = media - (rolling_std * deviation)

    return bb_upper, bb_lower


def detect_cross_bollinger_bands(stock_list, window, lower_bands, upper_bands):
    stock_list_hist = []
    lower_bands_hist = []
    upper_bands_hist = []

    buy_list = []
    sell_list = []
    buy_index_list = []
    sell_index_list = []
    signal_list = []

    for index in range(len(stock_list) - (window * 2), len(stock_list)):

        if len(stock_list) > window * 2:
            stock_list_hist.append(float(stock_list[index]))
            lower_bands_hist.append(float(lower_bands[index]))
            upper_bands_hist.append(float(upper_bands[index]))

            if len(signal_list) > 1:

                stock_price = float(stock_list[index])

                current_price = stock_list_hist[-1:]
                current_lower_band = lower_bands_hist[-1:]
                current_upper_band = upper_bands_hist[-1:]

                last_price = stock_list_hist[-2:-1]
                last_lower_band = lower_bands_hist[-2:-1]
                last_upper_band = upper_bands_hist[-2:-1]

                if current_price > current_lower_band and last_price <= last_lower_band:
                    buy_list.append(stock_price)
                    buy_index_list.append(index)
                    # 'Buy'
                    signal_list.append(1)


                elif current_price < current_upper_band and last_price >= last_upper_band:
                    sell_list.append(stock_price)
                    sell_index_list.append(index)
                    # 'Sell'
                    signal_list.append(2)

                else:
                    # 'Hold'
                    signal_list.append(0)

            else:
                # 'Hold'
                signal_list.append(0)

    return buy_list, sell_list, buy_index_list, sell_index_list, signal_list


def plot_signals_bollinger_bands_chart(ax, bollinger_buy, bollinger_sell, bollinger_index_buy, bollinger_index_sell):
    if len(bollinger_buy) > 0:
        ax.scatter(bollinger_index_buy, bollinger_buy, marker='v', color='red')
        for buy in range(len(bollinger_index_buy)):
            ax.text(bollinger_index_buy[buy], bollinger_buy[buy], ' - buy', color='black', alpha=.5)

    if len(bollinger_sell) > 0:
        ax.scatter(bollinger_index_sell, bollinger_sell, marker='^', color='green')
        for sell in range(len(bollinger_index_sell)):
            ax.text(bollinger_index_sell[sell], bollinger_sell[sell], ' - sell', color='black', alpha=.5)


def plot_max_min_price_chart(ax, min, max, average):
    text = "Summary\nMax: {}\nMin:  {}\nAvg:  {}".format(max, min, round(average, 2))

    add_anchored_text_chart(ax, text, loc=2)


def add_anchored_text_chart(ax, text, loc=2):
    fp = dict(size=9)
    at = AnchoredText(text, loc=loc, prop=fp)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)
    return at


def notify_cross_bollinger_bands(current_price, current_lower_band, current_upper_band, last_price, last_lower_band,
                                 last_upper_band):
    signal = None

    if current_price > current_lower_band and last_price <= last_lower_band:

        signal = 'Bollinger Band Lower Reached - BUY'

    elif current_price < current_upper_band and last_price >= last_upper_band:

        signal = 'Bollinger Band Upper Reached - SELL'

    if signal is not None:
        message = '{}. Price: {}. Time: {}'.format(signal, current_price, helper.get_current_date_hour_str())

        telegram_send.send(messages=[message])


def notify_cross_target_limits(current_price, target_min, target_max):
    signal = None

    if current_price >= target_min:

        signal = 'Minimum price reached'

    elif current_price <= target_max:

        signal = 'Maximum price reached'

    if signal is not None:
        message = '{}. Price: {}. Time: {}'.format(signal, current_price, helper.get_current_date_hour_str())

    telegram_send.send(messages=[message])


def send_message(message):
    msg_list = []

    msg_list.append("mensagem: " + helper.get_current_date_hour_str())

    for msg in msg_list:
        telegram_send.send(messages=[message])
        # print(msg)


def set_global_configs(configs_dict):
    global SOURCE_URL
    global STOCK_FILE

    global WEEKDAYS_EXECUTION
    global BEGIN_HOUR_EXECUTION
    global END_HOUR_EXECUTION

    global BOLLINGER_CALCULATION_WINDOW
    global BOLLINGER_STANDARD_DEVIATION

    global X_AXIS_VIEW_LIMIT
    global TARGET_PRICE_MINIMUM
    global TARGET_PRICE_MAXIMUM

    global SHOW_MAIN_CHART
    global SHOW_BOLLINGER_BANDS_CHART
    global SHOW_TARGET_PRICES_CHART
    global SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS
    global SEND_NOTIFICATION_CROSS_TARGET_PRICES

    global INTERVAL_BETEWEEN_RUNS
    global READ_LAST_LINES_STOCK_FILE

    SOURCE_URL = configs_dict['source_url']

    WEEKDAYS_EXECUTION = configs_dict['weekdays_execution']
    WEEKDAYS_EXECUTION = WEEKDAYS_EXECUTION.split('#')[0]
    WEEKDAYS_EXECUTION = eval(WEEKDAYS_EXECUTION)

    BEGIN_HOUR_EXECUTION = int(configs_dict['begin_hour_execution'])
    END_HOUR_EXECUTION = int(configs_dict['end_hour_execution'])
    BOLLINGER_CALCULATION_WINDOW = int(configs_dict['bollinger_calculation_window'])
    BOLLINGER_STANDARD_DEVIATION = float(configs_dict['bollinger_standard_deviation'])
    X_AXIS_VIEW_LIMIT = int(configs_dict['x_axis_view_limit'])
    TARGET_PRICE_MINIMUM = float(configs_dict['target_price_minimum'])
    TARGET_PRICE_MAXIMUM = float(configs_dict['target_price_maximum'])

    SHOW_MAIN_CHART = bool(int(configs_dict['show_main_chart']))
    SHOW_BOLLINGER_BANDS_CHART = bool(int(configs_dict['show_bollinger_bands_chart']))
    SHOW_TARGET_PRICES_CHART = bool(int(configs_dict['show_target_prices_chart']))
    SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS = bool(int(configs_dict['send_notification_cross_bollinger_bands']))
    SEND_NOTIFICATION_CROSS_TARGET_PRICES = bool(int(configs_dict['send_notification_cross_target_prices']))

    INTERVAL_BETEWEEN_RUNS = int(configs_dict['interval_beteween_runs'])

    READ_LAST_LINES_STOCK_FILE = int(configs_dict['read_last_lines_stock_file'])

    stock_filename = configs_dict['stock_filename']
    STOCK_FILE = helper.path_join(BASE_PATH, stock_filename)


def load_configs(config_file_path):
    set_global_configs(get_configs(config_file_path))


def get_stock_history(source_url, file_stock):
    current_price = get_last_stock_price_ADVN(source_url)
    save_stock_price(file_stock, current_price)


def check_execution(weekdays_execution, begin_hour_execution, end_hour_execution):
    return check_execution_day(weekdays_execution) and check_execution_hour(begin_hour_execution, end_hour_execution)


def clear():
    index = -10
    del BOLLINGER_SELL[:index]
    del BOLLINGER_BUY[:index]
    del BOLLINGER_INDEX_SELL[:index]
    del BOLLINGER_INDEX_BUY[:index]
    del BOLLINGER_SIGNAL[:index]


from pathlib import Path
from collections import deque


def get_stock_list(stock_file, last_lines):
    stock_prices = []
    stock_date = []
    stock_time = []

    if helper.file_exists(stock_file):
        stock_record = helper.read_last_lines_file(stock_file, last_lines)
        stock_prices = [p.split(';')[0] for p in stock_record]
        stock_time = [p.split(';')[2] for p in stock_record]

    return stock_prices, stock_date, stock_time


def main():
    df = pd.read_csv(STOCK_FILE, sep=';', names=['Stock', 'Date', 'Time'])

    stock_prices = df['Stock']
    # tock_date = df['Date']
    stock_time = df['Time']

    #stock_prices, _, stock_time = get_stock_list(STOCK_FILE, READ_LAST_LINES_STOCK_FILE)

    upper_band, lower_band = calc_bollinger_bands(stock_prices, BOLLINGER_CALCULATION_WINDOW,
                                                  BOLLINGER_STANDARD_DEVIATION)

    if upper_band is not None or lower_band is not None:
        BOLLINGER_BUY, BOLLINGER_SELL, BOLLINGER_INDEX_BUY, BOLLINGER_INDEX_SELL, BOLLINGER_SIGNAL = detect_cross_bollinger_bands(
            stock_prices, X_AXIS_VIEW_LIMIT, lower_band, upper_band)

    if SHOW_MAIN_CHART:

        plot_main_chart(axes, stock_prices, stock_time, X_AXIS_VIEW_LIMIT)
        plot_max_min_price_chart(axes, stock_prices.min(), stock_prices.max(), stock_prices.mean())

        if upper_band is not None or lower_band is not None:

            if SHOW_BOLLINGER_BANDS_CHART:
                plot_bollinger_bands_chart(axes, lower_band, upper_band)
                plot_signals_bollinger_bands_chart(axes, BOLLINGER_BUY, BOLLINGER_SELL, BOLLINGER_INDEX_BUY,
                                                   BOLLINGER_INDEX_SELL)

        if SHOW_TARGET_PRICES_CHART:
            plot_line_chart(axes, len(stock_prices), TARGET_PRICE_MINIMUM, 'blue', '.', 'Target Buy')
            plot_line_chart(axes, len(stock_prices), TARGET_PRICE_MAXIMUM, 'pink', '.', 'Target Sell')

        plt.legend(loc='best')
        # plt.show()
        plt.pause(1)

    if SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS:
        notify_cross_bollinger_bands(float(stock_prices[-1:]), float(lower_band[-1:]), float(upper_band[-1:]),
                                     float(stock_prices[-2:-1]),
                                     float(lower_band[-2:-1]), float(upper_band[-2:-1]))

    if SEND_NOTIFICATION_CROSS_TARGET_PRICES:
        notify_cross_target_limits(float(stock_prices[-1:]), TARGET_PRICE_MINIMUM, TARGET_PRICE_MAXIMUM)

    clear()


while True:

    try:
        load_configs(CONFIG_FILE_PATH)
    except Exception as e:
        msg = "FATAL ERROR SETTINGS. Error loading settings. Time: {}. Exception: {}".format(
            helper.get_current_date_hour_str(), e)
        print(msg)
        logging.critical(msg)
        send_message(msg)
        exit('FATAL ERROR SETTINGS')

    try:
        if check_execution(WEEKDAYS_EXECUTION, BEGIN_HOUR_EXECUTION, END_HOUR_EXECUTION):
            get_stock_history(SOURCE_URL, STOCK_FILE)
    except Exception as e:
        msg = "Error get stock. Time: {}. Exception: {}".format(helper.get_current_date_hour_str(), e)
        print(msg)
        logging.error(msg)

        helper.set_sleep(60)

    try:
        main()
        NUM_ERRORS_MAIN = 0
    except Exception as e:
        msg = "Error main function. Time: {}. Exception: {}".format(helper.get_current_date_hour_str(), e)
        print(msg)
        logging.error(msg)

        helper.set_sleep(60)
        NUM_ERRORS_MAIN += 1
        if NUM_ERRORS_MAIN > 5:
            msg = "FATAL ERROR MAIN. " + msg
            print(msg)
            logging.critical(msg)
            send_message(msg)
            exit('FATAL ERROR MAIN')

    print('Success.', helper.get_current_date_hour_str())
    helper.set_sleep(INTERVAL_BETEWEEN_RUNS - 1)
