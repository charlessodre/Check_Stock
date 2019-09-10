# Create by: Charles Sodré (https://github.com/charlessodre/Check_Stock)
# Date: 08/2019
# Based in course of Saulo Catharino: https://github.com/saulocatharino/machine_learning_for_traders
# Avalia uma ação para Compra e/ou Venda e envia uma notificação pelo Telegram caso o limiar de preço definido seja atingindo.
# Também notifica quando o valor da ação cruza as bandas de Bollinger.

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

from enum import Enum


class MarketStatus(Enum):
    OPEN = 1
    CLOSED = 2


logging.basicConfig(filename=helper.path_join('log', 'application_log.log'), level=logging.ERROR)

CONFIG_FILE_PATH = helper.path_join('config', 'config.txt')
BASE_PATH = 'base'
SOURCE_URL = None  # 'https://br.investing.com/equities/usiminas-pna'
STOCK_FILE = None
STOCK_NAME = None

INTERVAL_BETWEEN_RUNS = None  # 20
READ_LAST_LINES_STOCK_FILE = None  # 50

# [0 (Sunday), 1 (Monday) ... 6 (Saturday)].
WEEKDAYS_EXECUTION = None  # [1, 2, 3, 4, 5]
BEGIN_HOUR_EXECUTION = None  # 9
END_HOUR_EXECUTION = None  # 17
# This option overrides "begin_hour_execution" and  "end_hour_execution"
EXECUTION_BY_MARKET_STATUS = True
MARKET_STATUS = MarketStatus.CLOSED
PREVIOUS_CLOSING_PRICE = 0
OPEN_PRICE = 0
PRICE_VARIATION = 0

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

NUM_ERRORS_MAIN = 0
NUM_ERRORS_GET_PRICE = 0

BOLLINGER_SELL = []
BOLLINGER_BUY = []
BOLLINGER_INDEX_SELL = []
BOLLINGER_INDEX_BUY = []
BOLLINGER_SIGNAL = []

mpl.rcParams['toolbar'] = 'None'
fig = plt.figure(figsize=(16, 8))
fig.canvas.set_window_title('Stock Price History')
axes = fig.gca()


def get_configs(config_file_path):
    settings = {}

    configs = helper.read_file(config_file_path, 'r')
    for config in configs:
        if len(config.strip()) > 10:
            items = config.split('=')
            settings[items[0]] = items[1]

    return settings


def get_beautiful_soup(source_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    con = requests.get(source_url, headers=headers)

    # Status 200 Ok.
    # https://www.w3.org/Protocols/HTTP/1.1/draft-ietf-http-v11-spec-01#Status-Codes
    # con.status_code

    soup = BeautifulSoup(con.content, "html.parser")

    return soup


def get_last_stock_price_ADVN(soup):
    main_div = soup.find('div', {'id': 'quotes_summary_current_data'})

    sotck_price_tag = main_div.find('span', {'id': 'last_last'})

    stock_price = sotck_price_tag.text
    print(stock_price)

    if len(stock_price) > 4:  # TODO:  Teste
        logging.error('Valor Antes: ' + stock_price)  # TODO: Teste

    stock_price = stock_price.replace('.', '').replace(',', '.')

    print(stock_price)  # TODO:  Teste

    stock_price = float(stock_price)

    print(stock_price)  # TODO:  Teste

    return stock_price


def get_status_market_ADVN(soup):
    market_status = MarketStatus.CLOSED

    main_div = soup.find('div', {'id': 'quotes_summary_current_data'})

    status_div = main_div.find('div', {'class': 'bottom lighterGrayFont arial_11'})

    status_text = status_div.text

    if 'Fechado' not in status_text:
        market_status = MarketStatus.OPEN

    return market_status


def get_prices_open_closing_ADVN(soup):
    main_div = soup.find('div', {'id': 'quotes_summary_secondary_data'})

    previous_closing_price = main_div.find_all('span')[1].text
    previous_closing_price = previous_closing_price.replace('.', '').replace(',', '.')
    previous_closing_price = float(previous_closing_price)

    open_price = main_div.find_all('span')[3].text
    open_price = open_price.replace('.', '').replace(',', '.')
    open_price = float(open_price)

    return previous_closing_price, open_price


def get_price_variation_ADVN(soup):
    main_div = soup.find('div', {'id': 'quotes_summary_current_data'})

    variation_div = main_div.find('div', {'class': 'top bold inlineblock'})

    value_variation = variation_div.find_all('span')[3].text

    value_variation = value_variation.replace('%', '').replace('.', '').replace(',', '.')

    value_variation = float(value_variation)

    return value_variation


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
    if upper_band is not None or lower_band is not None:
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

    if lower_bands is not None or upper_bands is not None:

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


def plot_summary_price_chart(ax, stock_list):
    text = "Summary: Max: {} | Min: {} | Avg: {} | Std: {}".format(stock_list.max(), stock_list.min(),
                                                                   round(stock_list.mean(), 2),
                                                                   round(stock_list.std(), 2))

    add_anchored_text_chart(ax, text, 'lower left', (0., 1.))


def add_anchored_text_chart(ax, text, loc, bbox_anchor):
    at = AnchoredText(text, loc=loc, prop=dict(size=9), frameon=True,
                      bbox_to_anchor=bbox_anchor,
                      bbox_transform=ax.transAxes)

    ax.add_artist(at)
    return at


def plot_market_status(ax, market_status):
    text = "Market Status: {}".format(market_status.name)

    add_anchored_text_chart(ax, text, 'lower left', (0.3, 1.))


def plot_open_previous_closing_price(ax, open_price, previous_closing_price):
    text = "Previous Closing Price: {} | Open Price: {}".format(open_price, previous_closing_price)

    add_anchored_text_chart(ax, text, 'lower left', (0.45, 1.))


def plot_price_variation(ax, price_variation):
    text = "Var: {}%".format(price_variation)

    add_anchored_text_chart(ax, text, 'lower left', (0.72, 1.))


def notify_cross_bollinger_bands(current_price, current_lower_band, current_upper_band, last_price, last_lower_band,
                                 last_upper_band):
    signal = None

    if current_price > current_lower_band and last_price <= last_lower_band:

        signal = 'Bollinger Band Lower Reached - BUY'

    elif current_price < current_upper_band and last_price >= last_upper_band:

        signal = 'Bollinger Band Upper Reached - SELL'

    if signal is not None:
        message = '{}. Price: {}. Time: {}'.format(signal, current_price, helper.get_current_date_hour_str())
        send_message(message)


def notify_cross_target_limits(last_price, current_price, target_min, target_max):
    signal = None

    if current_price <= target_min and current_price < last_price:

        signal = 'Minimum price reached'

    elif current_price >= target_max and current_price > last_price:

        signal = 'Maximum price reached'

    if signal is not None:
        message = '{}. Price: {}. Time: {}'.format(signal, current_price, helper.get_current_date_hour_str())
        send_message(message)


def send_message(message):
    if type(message) is list:
        telegram_send.send(messages=message)
    else:
        telegram_send.send(messages=[message])


def set_global_configs(configs_dict):
    global SOURCE_URL
    global STOCK_FILE
    global STOCK_NAME
    global WEEKDAYS_EXECUTION
    global BEGIN_HOUR_EXECUTION
    global END_HOUR_EXECUTION
    global EXECUTION_BY_MARKET_STATUS

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

    global INTERVAL_BETWEEN_RUNS
    global READ_LAST_LINES_STOCK_FILE

    SOURCE_URL = configs_dict['source_url']
    STOCK_NAME = configs_dict['stock_name']

    WEEKDAYS_EXECUTION = configs_dict['weekdays_execution']
    WEEKDAYS_EXECUTION = WEEKDAYS_EXECUTION.split('#')[0]
    WEEKDAYS_EXECUTION = eval(WEEKDAYS_EXECUTION)

    BEGIN_HOUR_EXECUTION = int(configs_dict['begin_hour_execution'].split('#')[0])
    END_HOUR_EXECUTION = int(configs_dict['end_hour_execution'].split('#')[0])
    EXECUTION_BY_MARKET_STATUS = bool(int(configs_dict['execution_by_market_status'].split('#')[0]))

    BOLLINGER_CALCULATION_WINDOW = int(configs_dict['bollinger_calculation_window'].split('#')[0])
    BOLLINGER_STANDARD_DEVIATION = float(configs_dict['bollinger_standard_deviation'].split('#')[0])
    X_AXIS_VIEW_LIMIT = int(configs_dict['x_axis_view_limit'].split('#')[0])
    TARGET_PRICE_MINIMUM = float(configs_dict['target_price_minimum'].split('#')[0])
    TARGET_PRICE_MAXIMUM = float(configs_dict['target_price_maximum'].split('#')[0])

    SHOW_MAIN_CHART = bool(int(configs_dict['show_main_chart'].split('#')[0]))
    SHOW_BOLLINGER_BANDS_CHART = bool(int(configs_dict['show_bollinger_bands_chart'].split('#')[0]))
    SHOW_TARGET_PRICES_CHART = bool(int(configs_dict['show_target_prices_chart'].split('#')[0]))
    SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS = bool(
        int(configs_dict['send_notification_cross_bollinger_bands'].split('#')[0]))
    SEND_NOTIFICATION_CROSS_TARGET_PRICES = bool(
        int(configs_dict['send_notification_cross_target_prices'].split('#')[0]))

    INTERVAL_BETWEEN_RUNS = int(configs_dict['interval_between_runs_seconds'].split('#')[0])

    READ_LAST_LINES_STOCK_FILE = int(configs_dict['read_last_lines_stock_file'].split('#')[0])

    stock_filename = configs_dict['stock_filename']
    STOCK_FILE = helper.path_join(BASE_PATH, stock_filename)


def load_configs(config_file_path):
    set_global_configs(get_configs(config_file_path))


def get_stock_history(soup, file_stock):
    current_price = get_last_stock_price_ADVN(soup)
    save_stock_price(file_stock, current_price)


def check_execution(weekdays_execution, begin_hour_execution, end_hour_execution, execution_by_market_status,
                    market_status):
    exec = False
    if execution_by_market_status:
        exec = (market_status == MarketStatus.OPEN)
    else:
        exec = check_execution_day(weekdays_execution) and check_execution_hour(begin_hour_execution,
                                                                                end_hour_execution)
    return exec


def get_stock_list(stock_file, last_lines):
    stock_prices = []
    stock_date = []
    stock_time = []

    if helper.file_exists(stock_file):
        stock_record = helper.read_last_lines_file(stock_file, last_lines)
        stock_prices = [float(p.split(';')[0]) for p in stock_record]
        stock_time = [p.split(';')[2] for p in stock_record]

    return stock_prices, stock_date, stock_time


def main():
    stock_prices, _, stock_time = get_stock_list(STOCK_FILE, READ_LAST_LINES_STOCK_FILE)

    stock_prices = pd.Series(stock_prices)
    stock_time = pd.Series(stock_time)

    upper_band, lower_band = calc_bollinger_bands(stock_prices, BOLLINGER_CALCULATION_WINDOW,
                                                  BOLLINGER_STANDARD_DEVIATION)

    BOLLINGER_BUY, BOLLINGER_SELL, BOLLINGER_INDEX_BUY, BOLLINGER_INDEX_SELL, BOLLINGER_SIGNAL = detect_cross_bollinger_bands(
        stock_prices, X_AXIS_VIEW_LIMIT, lower_band, upper_band)

    if SHOW_MAIN_CHART:

        plot_main_chart(axes, stock_prices, stock_time, X_AXIS_VIEW_LIMIT)
        plot_summary_price_chart(axes, stock_prices)
        plot_market_status(axes, MARKET_STATUS)
        plot_open_previous_closing_price(axes, PREVIOUS_CLOSING_PRICE, OPEN_PRICE)
        plot_price_variation(axes, PRICE_VARIATION)

        if SHOW_BOLLINGER_BANDS_CHART:
            plot_bollinger_bands_chart(axes, lower_band, upper_band)
            plot_signals_bollinger_bands_chart(axes, BOLLINGER_BUY, BOLLINGER_SELL, BOLLINGER_INDEX_BUY,
                                               BOLLINGER_INDEX_SELL)

        if SHOW_TARGET_PRICES_CHART:
            plot_line_chart(axes, len(stock_prices), TARGET_PRICE_MINIMUM, 'blue', '.', 'Target Buy')
            plot_line_chart(axes, len(stock_prices), TARGET_PRICE_MAXIMUM, 'pink', '.', 'Target Sell')

        plt.suptitle(STOCK_NAME)

        plt.legend(bbox_to_anchor=(0., -.2, 1., .102), loc='upper left', ncol=5, mode="expand", borderaxespad=0.,
                   fontsize=9)
        # plt.show()
        plt.pause(1)

    if SEND_NOTIFICATION_CROSS_BOLLINGER_BANDS:
        if lower_band is not None or upper_band is not None:
            notify_cross_bollinger_bands(float(stock_prices[-1:]), float(lower_band[-1:]), float(upper_band[-1:]),
                                         float(stock_prices[-2:-1]),
                                         float(lower_band[-2:-1]), float(upper_band[-2:-1]))

    if SEND_NOTIFICATION_CROSS_TARGET_PRICES:
        notify_cross_target_limits(float(stock_prices[-2:-1]), float(stock_prices[-1:]), TARGET_PRICE_MINIMUM,
                                   TARGET_PRICE_MAXIMUM)


while True:

    try:
        load_configs(CONFIG_FILE_PATH)
    except Exception as e:
        msg = "FATAL ERROR SETTINGS. Error loading settings. Time: {}. Exception: {}".format(
            helper.get_current_date_hour_str(), e)
        print(msg)
        # logging.critical(msg)
        logging.exception(msg)
        send_message(msg)
        exit('FATAL ERROR SETTINGS')

    try:
        soup = get_beautiful_soup(SOURCE_URL)

        MARKET_STATUS = get_status_market_ADVN(soup)

        if check_execution(WEEKDAYS_EXECUTION, BEGIN_HOUR_EXECUTION, END_HOUR_EXECUTION, EXECUTION_BY_MARKET_STATUS,
                           MARKET_STATUS):
            get_stock_history(soup, STOCK_FILE)
            PREVIOUS_CLOSING_PRICE, OPEN_PRICE = get_prices_open_closing_ADVN(soup)
            PRICE_VARIATION = get_price_variation_ADVN(soup)


    except Exception as e:
        msg = "Error get stock. Time: {}. Exception: {}".format(helper.get_current_date_hour_str(), e)
        print(msg)
        logging.error(msg)
        helper.set_sleep(60)
        NUM_ERRORS_GET_PRICE += 1
        if NUM_ERRORS_GET_PRICE == 10:
            msg = "FATAL ERROR GET PRICE. " + msg
            print(msg)
            # logging.critical(msg)
            logging.exception(msg)
            send_message(msg)
            exit('FATAL ERROR GET PRICE')

    try:
        main()
        NUM_ERRORS_MAIN = 0

    except Exception as e:
        msg = "Error main function. Time: {}. Exception: {}".format(helper.get_current_date_hour_str(), e)
        print(msg)
        logging.error(msg)

        helper.set_sleep(60)
        NUM_ERRORS_MAIN += 1
        if NUM_ERRORS_MAIN == 3:
            msg = "FATAL ERROR MAIN. " + msg
            print(msg)
            # logging.critical(msg)
            logging.exception(msg)
            send_message(msg)
            exit('FATAL ERROR MAIN')

    print('Success.', helper.get_current_date_hour_str())
    helper.set_sleep(INTERVAL_BETWEEN_RUNS - 1)
