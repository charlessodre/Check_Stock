# Importação das bibliotecas
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import helper

exibe_ultimos_registros = 50

file_path = 'base'
file_stock_name = 'USIM5.csv'
file_stock = helper.path_join(file_path, file_stock_name)

begin_hour = 9
end_hour = 17

window = 20
deviation = 2
target_price_buy = 7.6
target_price_sell = 7.3

fig = plt.figure(figsize=(16, 8))
fig.canvas.set_window_title('Acompanhamento value Ação')
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


# def plot_bollinger_bands_chart(ax, stock_list, window, deviation):
#     if len(stock_list) > window:
#         media = stock_list.rolling(window=window).mean()
#         rolling_std = stock_list.rolling(window=window).std()
#
#         upper_band = media + (rolling_std * deviation)
#         lower_band = media - (rolling_std * deviation)
#
#         ax.plot(upper_band, '--', color="green", alpha=.5, label='BB Up')
#         ax.plot(lower_band, '--', color="red", alpha=.5, label='BB Down')
#
#         return lower_band, upper_band


def plot_bollinger_bands_chart(ax, upper_band, lower_band):
    ax.plot(upper_band, '--', color="green", alpha=.5, label='BB Up')
    ax.plot(lower_band, '--', color="red", alpha=.5, label='BB Down')


def plot_line_chart(ax, list_size, value, color_name, marker="*", legend=None, alpha=0.5):
    lim = np.empty(list_size)
    lim.fill(value)
    ax.plot(lim, marker, color=color_name, alpha=alpha, label=legend)


def calc_bollinger_bands_chart(ax, stock_list, window, deviation):
    if len(stock_list) > window:
        media = stock_list.rolling(window=window).mean()
        rolling_std = stock_list.rolling(window=window).std()

        upper_band = media + (rolling_std * deviation)
        lower_band = media - (rolling_std * deviation)

    return lower_band, upper_band


def detect_cross_bollinger_bands(stock_list, lower_bands, upper_bands):
    current_price = stock_list[-1:]
    current_lower_band = lower_bands[-1:]
    current_upper_band = upper_bands[-1:]
    last_price = stock_list[-1:-2]
    last_lower_band = lower_bands[-1:-2]
    last_upper_band = upper_bands[-1:-2]

    if current_price > current_lower_band and last_price <= last_lower_band:
        print('Buy')

    elif current_price < current_upper_band and last_price >= last_upper_band:
        print('Sell')
    else:
        print('Hold')

    # ax.scatter(stock_list, stock_list, marker='^', color='green')
    return None


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

    if check_execution_hour(begin_hour, end_hour):
        list_cross_bb_upper = []
        list_cross_bb_lower = []

        # plt.ioff()

        print('Getting...')
        last_price = get_last_stock_price_ADVN()
        save_stock_price(file_stock, last_price)

        df = pd.read_csv(file_stock, sep=';', names=['Stock', 'Date', 'Time'])

        stock_prices = df['Stock']
        stock_date = df['Date']
        stock_time = df['Time']

        plot_main_chart(axes, stock_prices, stock_time, window)

        #lower_band, upper_band = plot_bollinger_bands_chart(axes, stock_prices, window, deviation)
        lower_band, upper_band = calc_bollinger_bands_chart(axes, stock_prices, window, deviation)

        list_cross_bb_upper.append(upper_band)
        list_cross_bb_lower.append(lower_band)

        plot_bollinger_bands_chart(axes, lower_band, upper_band)


        plot_line_chart(axes, len(stock_prices), target_price_buy, 'blue', '.', 'Target Buy')
        plot_line_chart(axes, len(stock_prices), target_price_sell, 'pink', '.', 'Target Sell')

        plot_max_min_price_chart(axes, stock_prices.min(), stock_prices.max(), stock_prices.mean())

        #detect_cross_bollinger_bands(stock_prices, lower_band, upper_band)

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
