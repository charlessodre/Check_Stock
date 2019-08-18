# Importação das bibliotecas
import requests 
from bs4 import BeautifulSoup 
import pandas as pd 
import re


#Trata o seprador decimal.
def substitueSeparadorDecimal(string, atual, novo):
    string = str(string).replace(',','v')
    string = string.replace('.',',')
    string = string.replace('v','.')

# url dos histórico dos papeis
url_fonte = 'https://br.investing.com/equities/usiminas-pna'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

# Conectando da página
con = requests.get(url_fonte, headers=headers)

# Status da Conexão. Status 200 conexão Ok.
#https://www.w3.org/Protocols/HTTP/1.1/draft-ietf-http-v11-spec-01#Status-Codes
con.status_code

# Cria objeto BeautifulSoup com o conteúdo html da página
soup = BeautifulSoup(con.content, "html.parser")
#print(soup.prettify())

#Extraindo a Div principal que contém a div onde está o valor da ação.
div_principal = soup.find('div', {'id':'quotes_summary_current_data'})
#type(div_principal)
#print(div_principal)

#d = div_principal.find('div', {'class': 'inlineblock'})

# Extrai a tag que contém o valor da ação.
tag_valor_acao = div_principal.find('span', {'id': 'last_last'})

# Extrai o valor da ação existente na tag
valor_acao = tag_valor_acao.text

valor_acao = float(valor_acao)

