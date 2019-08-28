# Create by: Charles Sodré (https://github.com/charlessodre/Check_Stock)
# Date: 08/2019
# Based in course of Saulo Catharino: https://github.com/saulocatharino/machine_learning_for_traders
#


# Library Import
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import helper

file_path = 'base'
file_stock_name = 'USIM5.csv'
file_stock = helper.path_join(file_path, file_stock_name)

weekdays_execution = [1, 2, 3, 4, 5]  # [0 (Sunday), 1 (Monday) ... 6 (Saturday)].
begin_hour_execution = 9
end_hour_execution = 17

window = 40
deviation = 2
target_price_buy = 7.6
target_price_sell = 7.3

bollinger_sell = []
bollinger_buy = []
bollinger_index_sell = []
bollinger_index_buy = []
bollinger_signal = []

fig = plt.figure(figsize=(16, 8))
fig.canvas.set_window_title('Acompanhamento Valor Ação')
fig.suptitle('USIM5')
axes = fig.gca()


def get_last_stock_price_ADVN():
    source_url = 'https://br.investing.com/equities/usiminas-pna'
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

    plt.xticks(rotation=90)


def plot_bollinger_bands_chart(ax, upper_band, lower_band):
    ax.plot(upper_band, '--', color="green", alpha=.2, label='BB Up')
    ax.plot(lower_band, '--', color="red", alpha=.2, label='BB Down')


def plot_line_chart(ax, list_size, value, color_name, marker="*", legend=None, alpha=0.5):
    lim = np.empty(list_size)
    lim.fill(value)
    ax.plot(lim, marker, color=color_name, alpha=alpha, label=legend)


def calc_bollinger_bands(ax, stock_list, window, deviation):
    if len(stock_list) > window:
        media = stock_list.rolling(window=window).mean()
        rolling_std = stock_list.rolling(window=window).std()

        upper_band = media + (rolling_std * deviation)
        lower_band = media - (rolling_std * deviation)

    return lower_band, upper_band


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
                signal_list.append(1)
                print('Buy')

            elif current_price < current_upper_band and last_price >= last_upper_band:
                sell_list.append(stock_price)
                sell_index_list.append(index)
                signal_list.append(2)
                print('Sell')
            else:
                signal_list.append(0)
                print('Hold')
        else:
            signal_list.append(0)
            print('Hold')

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


while True:
    # if check_execution_day(weekdays_execution) and check_execution_hour(begin_hour_execution, end_hour_execution):
    list_cross_bb_upper = []
    list_cross_bb_lower = []

    # plt.ioff()

    print('Getting...')
    # last_price = get_last_stock_price_ADVN()
    # save_stock_price(file_stock, last_price)

    df = pd.read_csv(file_stock, sep=';', names=['Stock', 'Date', 'Time'])

    stock_prices = df['Stock']
    stock_date = df['Date']
    stock_time = df['Time']

    plot_main_chart(axes, stock_prices, stock_time, window)

    lower_band, upper_band = calc_bollinger_bands(axes, stock_prices, window, deviation)

    plot_bollinger_bands_chart(axes, lower_band, upper_band)

    plot_line_chart(axes, len(stock_prices), target_price_buy, 'blue', '.', 'Target Buy')
    plot_line_chart(axes, len(stock_prices), target_price_sell, 'pink', '.', 'Target Sell')

    plot_max_min_price_chart(axes, stock_prices.min(), stock_prices.max(), stock_prices.mean())

    bollinger_buy, bollinger_sell, bollinger_index_buy, bollinger_index_sell, bollinger_signal = detect_cross_bollinger_bands(
        stock_prices, window, lower_band, upper_band)

    plot_signals_bollinger_bands_chart(axes, bollinger_buy, bollinger_sell, bollinger_index_buy, bollinger_index_sell)

    print('Sucesss.', helper.get_current_date_hour_str())

    plt.legend(loc='best')
    plt.show()

    helper.set_sleep(18)

# lista_registro_acao = lista_registro_acao[-exibe_ultimos_registros:]
# stock_prices = [float(value.split(';')[0]) for value in lista_registro_acao]
# stock_time = [time.split(';')[1] for time in lista_registro_acao]
# stock_prices = np.array(stock_prices)

# try:
#     last_price = obtem_ultimo_valor_acao()
#     salva_valor_acao(stock_file, last_price)
#
#     plota(stock_file)
#
#     print('Sucesss.', helper.get_current_date_hour_str())
#
#     helper.set_sleep(20)
# except:
#     print("Erro no servidor. Hora do Erro: ", helper.get_current_date_hour_str())
#     helper.set_sleep(60)
