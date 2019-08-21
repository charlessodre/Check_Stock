# Importação das bibliotecas
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import helper

path_arquivo = 'base'
nome_arquivo_acao = 'USIM5.csv'
arquivo_acao = helper.path_join(path_arquivo, nome_arquivo_acao)

exibe_ultimos_registros = 50
janela = 20
desvio = 2
valor_alvo_compra = 7.6
valor_alvo_venda = 7.3

fig = plt.figure(figsize=(16, 8))
fig.canvas.set_window_title('Acompanhamento value Ação')
fig.suptitle('USIM5')
ax = fig.gca()


def get_last_stock_price():
    # url dos histórico dos papeis
    source_url = 'https://br.investing.com/equities/usiminas-pna'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    # Conectando da página
    con = requests.get(source_url, headers=headers)

    # Status da Conexão. Status 200 conexão Ok.
    # https://www.w3.org/Protocols/HTTP/1.1/draft-ietf-http-v11-spec-01#Status-Codes
    con.status_code

    # Cria objeto BeautifulSoup com o conteúdo html da página
    soup = BeautifulSoup(con.content, "html.parser")
    # print(soup.prettify())

    # Extraindo a Div principal que contém a div onde está o value da ação.
    main_div = soup.find('div', {'id': 'quotes_summary_current_data'})

    # Extrai a tag que contém o value da ação.
    sotck_price_tag = main_div.find('span', {'id': 'last_last'})

    # Extrai o value da ação existente na tag
    stock_price = sotck_price_tag.text

    # Trato o value (substitui vírgula por ponto)
    stock_price = stock_price.replace('.', '').replace(',', '.')

    stock_price = float(stock_price)

    return stock_price

def save_stock_price(stock_file, price):
    stock_price_list = []

    if helper.file_exists(stock_file):
        stock_price_list = helper.read_file(stock_file)

    registro_acao = '{};{};{}'.format(price, helper.get_current_date_str(), helper.get_current_hour())
    stock_price_list.append(registro_acao)

    helper.save_list_to_file(stock_file, stock_price_list, mode='w')

def get_stock_list(stock_file):
    lista_registro_acao = []
    if helper.file_exists(stock_file):
        lista_registro_acao = helper.read_file(stock_file)

    return lista_registro_acao

def verifica_horario_execucao():
    horaInicio = 9
    horaFim = 17

    hora_atual = int(helper.get_hour())

    return hora_atual >= horaInicio and hora_atual <= horaFim


def plot_graph(value, time):

    ax.clear()
    #ax.set(xlabel='time (s)', ylabel='USIM5', title='Acompanhamento value Ação')
    ax.plot(time, value)

    plt.xticks(rotation=90)
    bollinger_bands(value, janela, desvio)


def bollinger_bands(stock_list, window, deviation):

    if len(stock_list) > window:
        media = stock_list.rolling(window=window).mean()
        rolling_std = stock_list.rolling(window=window).std()

        upper_band = media + (rolling_std * deviation)
        lower_band = media - (rolling_std * deviation)

        ax.plot(upper_band, '--', color="green", alpha=.5)
        ax.plot(lower_band, '--', color="red", alpha=.5)

        ax.set_xlim(len(stock_list) - window * 2, len(stock_list) + 5)

        return lower_band, upper_band


def plot_line_chart(list_size, value, color_name):
    lim = np.empty(list_size)
    lim.fill(value)
    ax.plot(lim, '*', color=color_name, alpha=.5)


def detect_cross(stock_list, lower_band, upper_band, index):
    return None


while True:

    last_price = get_last_stock_price()
    save_stock_price(arquivo_acao, last_price)

    df = pd.read_csv(arquivo_acao, sep=';', names=['Stock', 'Date',  'Time'])

    #lista_registro_acao = lista_registro_acao[-exibe_ultimos_registros:]

    #stock_prices = [float(value.split(';')[0]) for value in lista_registro_acao]
    #stock_time = [time.split(';')[1] for time in lista_registro_acao]

    #stock_prices = np.array(stock_prices)

    stock_prices = df['Stock']
    stock_date = df['Date']
    stock_time = df['Time']

    plot_graph(stock_prices, stock_time)
    plot_line_chart(len(stock_prices), valor_alvo_compra, 'blue')
    plot_line_chart(len(stock_prices), valor_alvo_venda, 'pink')

    print('Sucesss.', helper.get_current_date_hour_str())
    plt.pause(2)
    helper.set_sleep(20)



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

