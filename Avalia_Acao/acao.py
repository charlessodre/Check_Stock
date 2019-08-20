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

fig = plt.figure(figsize=(16, 8))
fig.canvas.set_window_title('Acompanhamento valor Ação')
fig.suptitle('USIM5')
ax = fig.gca()


def obtem_ultimo_valor_acao():
    # url dos histórico dos papeis
    url_fonte = 'https://br.investing.com/equities/usiminas-pna'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    # Conectando da página
    con = requests.get(url_fonte, headers=headers)

    # Status da Conexão. Status 200 conexão Ok.
    # https://www.w3.org/Protocols/HTTP/1.1/draft-ietf-http-v11-spec-01#Status-Codes
    con.status_code

    # Cria objeto BeautifulSoup com o conteúdo html da página
    soup = BeautifulSoup(con.content, "html.parser")
    # print(soup.prettify())

    # Extraindo a Div principal que contém a div onde está o valor da ação.
    div_principal = soup.find('div', {'id': 'quotes_summary_current_data'})

    # Extrai a tag que contém o valor da ação.
    tag_valor_acao = div_principal.find('span', {'id': 'last_last'})

    # Extrai o valor da ação existente na tag
    valor_acao = tag_valor_acao.text

    # Trato o valor (substitui vírgula por ponto)
    valor_acao = valor_acao.replace('.', '').replace(',', '.')

    valor_acao = float(valor_acao)

    return valor_acao


def salva_valor_acao(arquivo_acao, valor_acao):
    lista_registro_acao = []

    if helper.file_exists(arquivo_acao):
        lista_registro_acao = helper.read_file(arquivo_acao)

    registro_acao = '{};{}'.format(valor_acao, helper.get_current_hour())
    lista_registro_acao.append(registro_acao)

    helper.save_list_to_file(arquivo_acao, lista_registro_acao, mode='w')

def obtem_lista_registro_acao(arquivo_acao):
    lista_registro_acao = []
    if helper.file_exists(arquivo_acao):
        lista_registro_acao = helper.read_file(arquivo_acao)

    return lista_registro_acao

def verifica_horario_execucao():
    horaInicio = 9
    horaFim = 17

    hora_atual = int(helper.get_hour())

    return hora_atual >= horaInicio and hora_atual <= horaFim



def plota_grafico_acao(valor, horario):

    ax.clear()
    #ax.set(xlabel='time (s)', ylabel='USIM5', title='Acompanhamento valor Ação')
    ax.plot(horario, valor)

    plt.xticks(rotation=90)
    plt.pause(5)

while True:

    #ultimo_valor = obtem_ultimo_valor_acao()
    #salva_valor_acao(arquivo_acao, ultimo_valor)

    lista_registro_acao = obtem_lista_registro_acao(arquivo_acao)

    lista_registro_acao = lista_registro_acao[-exibe_ultimos_registros:]

    valores_acao = [valor.split(';')[0] for valor in lista_registro_acao]
    horario_acao = [valor.split(';')[1] for valor in lista_registro_acao]

    plota_grafico_acao(valores_acao, horario_acao)

    print('Sucesso.', helper.get_current_date_hour_str())

    helper.set_sleep(20)



    # try:
    #     ultimo_valor = obtem_ultimo_valor_acao()
    #     salva_valor_acao(arquivo_acao, ultimo_valor)
    #
    #     plota(arquivo_acao)
    #
    #     print('Sucesso.', helper.get_current_date_hour_str())
    #
    #     helper.set_sleep(20)
    # except:
    #     print("Erro no servidor. Hora do Erro: ", helper.get_current_date_hour_str())
    #     helper.set_sleep(60)

