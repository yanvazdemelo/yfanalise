#!/usr/bin/env python
# coding: utf-8

# # Importando pacotes

# In[1]:


################################################## Trazendo os pacotes de fora ###################################
import importlib

def install_and_import(package):
    try:
        importlib.import_module(package)  # Tenta importar o pacote
    except ImportError:
        print(f"{package} não está instalado. Instalando agora...")
        get_ipython().system('pip install {package}  # Instala o pacote')
    finally:
        globals()[package] = importlib.import_module(package)  # Importa o pacote
        
        
install_and_import('sklearn')
install_and_import('numpy')
install_and_import('statsmodels')
install_and_import('seaborn')
install_and_import('oauth2client')

'''!pip install wbdata
!pip install -- update pandas
!pip install pandas_datareader
!pip install gspread
!pip install oauth2client
!pip install openpyxl
!pip install --update yfinance
!pip install selenium
!pip install -- update newspaper3k
!pip install -- update requests
!pip install bs4
!pip install -- update transformers
!pip install googletrans==3.1.0a0'''


# In[2]:


###################################### Importando bibliotecas ######################################

import os
os.environ['PYTHONHASHSEED'] = '0' # Remove os erros de cache persistente

import gspread
import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
from sklearn import datasets
import seaborn as sns
from oauth2client.service_account import ServiceAccountCredentials
import openpyxl
from sklearn.metrics import r2_score
import numpy as np
import sklearn
import yfinance as yf
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
import sqlite3
import pandas_datareader as pdr
import wbdata
import requests
from bs4 import BeautifulSoup
import newspaper
import sys
from transformers import T5Tokenizer
from transformers import T5Model, T5ForConditionalGeneration
from googletrans import Translator


# # Plano de escrita
# > Abaixo descreveremos quais são os objetivos desse algorítimo e quais passos serão utilizados para a realização dele.

# ## Objetivo principal
# > Esse algoritimo busca a análise econômica dos países da América do Sul produzindo um reporte que será acessado através de uma plataforma de visualização de dados.
# 
# ## Objetivos específicos
# 1. Coletar, armazenar e processar dados das principais empresas dos países selecionados através do Yahoo Finance
#     1.1 Além das empresas nacionais, é importante também produzir dados de empresas transnacionais relevantes para a região
# 2. Coletar, armazenar e processar dados macroeconômicos dos países relevantes através de alguma ferramenta
# 3. Coletar as principais notícias nos jornais nacionais dos países em questão e através de uma inteligência artifical gerar resumos dessas notícias para serem apresentados no reporte
# 
# ## Descrição das etapas pretendidas
# - Criação de um sistema de coleta, armazenamento local e consulta de dados dos ativos selecionados
#     - Os ativos relevantes são: cestas das bolsas de valores locais, taxa de câmbio com o dólar e em um escopo de região vamos extrair também os preços de commodities
#     - O armazenamento será através de um Banco de Dados. **Será utilizado o SQLite***
#     - Parte do processo de armazenamento é estabelecer um sistema eficiênte de datas para não sobrecarregar o yf
#     - O armazenamento é pensado como um Banco de Dados SQL
#     - Criar sistema de download dos dados históricos sem sobrecarregar YF
# - À partir dos dados obtidos executar os processamentos relevantes
#     - Executar análise do desvio padrão, correlação entre as bolsas, etc
#     - **Bonus:** Buscar bibliotecas que façam análise de risco e estudar ligeiramente as teorias dos ativos
#     - Armazenar todos os dados localmente
# - Organizar os dados em planilhas com conteúdo compatível com o software de visualização dos dados
#     - O software de visualização dos dados escolhi no momento foi o **Google Data Stuidio*
#     - Relevante aprender a utilizar
# - Utilizar a biblioteca de interação com o Drive para fazer o upload para uma pasta no drive que alimentará google data studio
# - Buscar e raspar principais notícias do dia e criar um resumo direcionado ao país através da IA
# - Armazenar localmente de forma compacta e fazer upload para o drive onde alimentará também o Google Data Studio
# - A ideia geral da visualização dos dados no google data stuidio é: 
#     - Resumo geral da região
#         - Principais variações regionais em ativos de bolsa
#         - Commodities
#         - Agregados e a última data de atualização
#         - Principais cestas de bolsa
#         - Tabela com as taxas de câmbio e variações
#         - Resumo das notícias locais em um pequeno resumo da região
#     - Resumo individual
#         - Descrição detalhada dos agregados
#         - Análise de nível médio de detalhe das ações relevantes pra unidade nacional
#         - Resumo de três parágrafos das três primeiras notícias das manchetes

# # Documentações e Links relevantes 
# 
# Código da IA: https://stackoverflow.com/questions/77816871/error-with-linux-for-google-api-gemini-ai
# Documentação do YF: https://pypi.org/project/yfinance/

# # Informações sobre os dados:
# 
#  

#    ## Sobre moedas:
#     Brasil (BRL): Real
#     Argentina (ARS): Peso argentino
#     Chile (CLP): Peso chileno
#     Colômbia (COP): Peso colombiano
#     México (MXN): Peso mexicano
#     Peru (PEN): Sol peruano
#     Uruguai (UYU): Peso uruguaio
#     Venezuela (VES): Bolívar soberano
#     Belize: Dólar de Belize (BZD)
#     Costa Rica: Colón costa-riquenho (CRC)
#     Guatemala: Quetzal guatemalteco (GTQ)
#     Honduras: Lempira hondurenho (HNL)
#     Nicarágua: Córdoba nicaraguense (NIO)
#     Panamá: Balboa panamenho (PAB)

# # Sistemas

# In[3]:


# Sistema de data

today = datetime.today()
today = today.strftime("%Y-%m-%d")

print(today)

def printype(ty):
    print(ty)
    print(type(ty))


# In[4]:


# Recuperar tabelas do BD SQL em um objeto pandas

def sqltodf(pandas):
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect('yfhistoric.db')
    # Consulta SQL para recuperar os dados da tabela
    query = f"SELECT * FROM {pandas}"
    # Ler os dados do banco de dados para um DataFrame do pandas
    df = pd.read_sql_query(query, conn)
    # Fechar a conexão com o banco de dados
    conn.close()
    return df


# In[5]:


### FUNÇÃO PARA RESGATAR A DATA CORRETA DE ATUALIZAÇÃO

# Tentei integrar essa função no meu código sem ter que abrir e fechar o DB a caba iteração, mas não soube. 

'''commcode = "HYMTF" #"HYMTF" #PRT não tem date @@@@@@@@@@@@@@@@ SÓ PARA UM TESTE'''
todaydelta = datetime.strptime(today, "%Y-%m-%d")
tenyragodelta = todaydelta - timedelta(days=10*365)
tenyragovar = tenyragodelta.strftime("%Y-%m-%d")
todayvar = todaydelta.strftime("%Y-%m-%d")
todaydt = datetime.strptime(today, "%Y-%m-%d")


#####
def datecheck(commcode):
    conn = sqlite3.connect('yfhistoric.db')
    cursor = conn.cursor()
    print(f"@@@@@@@@@@@@@@@@@@@@@@ REPORTE DO TICKER '{commcode}' @@@@@@@@@@@@@@@@")
    noatt = "no att" # PARA QUANDO A INSTRUÇÃO SEJA NÃO ATUALIZAR 
    commcode = commcode.lower()
    command = f'SELECT MIN(date) FROM "{commcode}"'
    cursor.execute(command)
    lastdate = cursor.fetchall()
    lastdate = [row[0] for row in lastdate]
    lastdatetest = f'{lastdate[0]}'
    # Testando se está vazio
    if lastdatetest == "None":
        print("é none") ######### AQUI COLOCAR 10 ANOS ATRÁS
        return tenyragovar
    else: # FAZER A DIFERENÇA DE TEMPO
        print("não é none, fazendo subtração")
        print(f"lastdatetest é {lastdatetest}")
        lastdatedt = datetime.strptime(lastdatetest, "%Y-%m-%d %H:%M:%S")
        timedif = lastdatedt - tenyragodelta
        if lastdatedt > tenyragodelta: # SE A LASTDATE FOR MAIOR (MAIS NOVA, MAIS RECENTE) VAI ATIVAR ESSE. ESSE TESTE É "QUAL DATA É MAIS RECENTE?"
            print("SE A LAST DATE FOR MAIS RECENTE QUE 10 ANOS ATRÁS, VAMOS ATUALIZAR E COMPLETAR OS 10 ANOS") # SE A LAST DATE FOR MAIS RECENTE QUE 10 ANOS ATRÁS, VAMOS ATUALIZAR E COMPLETAR OS 10 ANOS
            return tenyragovar
        else: # SE NÃO VAI ATIVAR ESSE, OU SEJA, A LASTDATE É MENOR OU IGUAL A "DEZ ANOS ATRÁS".
            print("TEM MAIS DE 10 ANOS DE REGISTRO JÁ, VER AGORA QUAL A ÚLTIMA DATA") # TEM MAIS DE 10 ANOS DE REGISTRO JÁ, VER AGORA QUAL A ÚLTIMA DATA
            command = f'SELECT MAX(date) FROM "{commcode}"'
            cursor.execute(command)
            earlydate = cursor.fetchall()
            earlydate = [row[0] for row in earlydate]
            earlydate = f'{earlydate[0]}'
            earlydatedt = datetime.strptime(earlydate, "%Y-%m-%d %H:%M:%S")
            earlydate = datetime.strftime(earlydatedt, "%Y-%m-%d")
            if earlydatedt == todaydt:
                print(f"{commcode} do not need att")
                return noatt
            else:
                print(f"Att from {earlydatedt} to {todaydt}")
                return earlydate

    conn.close()

'''##############
print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ISSO É UM TESTE@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

datetest = datecheck(commcode)

print(datetest)'''


# # Atualizações/Instalações

# In[6]:


# Criar/conectar um BD

# Primeiro é importante verificar se o arquivo do database está presente no "root" da instalação

rootdire =  os.getcwd()
rootdire_list = os.listdir(rootdire)

if 'yfhistoric.db' in rootdire_list:
    conexao = sqlite3.connect('yfhistoric.db')
    print('Você já tem um Banco de Dados')
else:
    conexao = sqlite3.connect('yfhistoric.db')
    print('Criando um banco de dados')
    cursor = conexao.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS indicators(
        id INTEGER PRIMARY KEY,
        datatype TEXT NOT NULL
    )
    ''')
    conexao.close()

### CRIANDO AS TABELAS SE ELAS NÃO EXISTEM ###
conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

###### TABELAS MÃE #####
cursor.execute('''
    CREATE TABLE IF NOT EXISTS indicators(
        id INTEGER PRIMARY KEY,
        datatype TEXT NOT NULL
    );
    
    ''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS texts(
        id INTEGER PRIMARY KEY,
        datatype TEXT NOT NULL
    );    
    ''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS countries( 
        id INTEGER PRIMARY KEY,
        country TEXT,
        alpha3code TEXT,
        latam TEXT
        
    );    
    ''')
# Na chave "latam" adicionar "yes", "no" e "world" 


cursor.execute('''
    CREATE TABLE IF NOT EXISTS niche( 
        id INTEGER PRIMARY KEY,
        niche TEXT
    );    
    ''')

##### TABELAS FILHA
cursor.execute('''
    CREATE TABLE IF NOT EXISTS currencies(
        id INTEGER PRIMARY KEY,
        currcode TEXT NOT NULL,
        currname TEXT NOT NULL,
        country TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES indicators(datatype)
        FOREIGN KEY (country) REFERENCES countries(country)
    );    
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY,
        ticcode TEXT NOT NULL,
        ticname TEXT NOT NULL,
        ticcat TEXT NOT NULL,
        datatype TEXT NOT NULL,
        country TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES indicators(datatype)
        FOREIGN KEY (country) REFERENCES countries(country)
    );    
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS commodities(
        id INTEGER PRIMARY KEY,
        commcode TEXT NOT NULL,
        comname TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES indicators(datatype)
    );    
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS agregates(
        id INTEGER PRIMARY KEY,
        agrcode TEXT NOT NULL,
        agrcodewb TEXT NOT NULL,
        agrname TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES indicators(datatype)
    );    
    ''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS cripto(
        id INTEGER PRIMARY KEY,
        criptoname TEXT NOT NULL, 
        criptocode TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES text(datatype)
    );    
    ''')

####### text

cursor.execute('''
    CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY,
        newspapername TEXT NOT NULL,
        newspaperlink TEXT NOT NULL,
        country TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES text(datatype)
        FOREIGN KEY (country) REFERENCES countries(country)
    );    
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS summary(
        id INTEGER PRIMARY KEY,
        summhierarquy TEXT NOT NULL, 
        country TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES text(datatype)
        FOREIGN KEY (country) REFERENCES countries(country)
    );    
    ''')



###### TESTES E END
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
table = cursor.fetchall()


conn.commit()
conn.close()

# print(rootdire      , ' !!!!! ', rootdire_list)  Para verificar
#print(rootdire      , ' !!!!! ', rootdire_list)


# Conectar ao banco de dados (isso criará o banco de dados se não existir)
# conexao = sqlite3.connect('yfhistoric.db')


# In[7]:


########## GATILHOS DAS CATEGORIAS MÃE (INCOMPLETO, FAZER DEPOIS)
conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

indicatorsdt = ('currencies', 'tickets', 'commodities', 'agregates')

textdt = ('news', 'summary')

countriescat = ('Brasil', 'Argentina', 'Chile', 'Colômbia', 'México', 'Peru', 'Uruguai', 'Venezuela', 'Belize', 'Costa Rica', 'Estados Unidos', 'Guatemala', 'Honduras', 'Nicarágua', 'Bolívia', 'Mundo', 'Criptomoeda', 'União Europeia')

conn.close()


# In[8]:


##### INSERIR DADOS TABELA MÃE


data = (indicatorsdt, textdt, countriescat)

conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

for indi in indicatorsdt:
    command = '''
        INSERT INTO indicators (datatype)
        SELECT ? AS datatype
        WHERE NOT EXISTS (
            SELECT 1 FROM indicators WHERE datatype = ?
        )
    '''
    conn.execute(command, (indi, indi))
    conn.commit()

for dt in textdt:
    command = '''
        INSERT INTO texts (datatype)
        SELECT ? AS datatype
        WHERE NOT EXISTS (
            SELECT 1 FROM indicators WHERE datatype = ?
        )
    '''
    conn.execute(command, (dt, dt))
    conn.commit()


# # TABELAS FILHAS/NETAS

# # Currencies

# In[9]:


##### CURRENCIES
currencies_todf = {  # EDITAR ISSO PARA ADICIONAR OU REMOVER MOEDAS RELEVANTES A SEREM ANALISADAS
    
'pais': ['Brasil', 'Argentina', 'Chile', 'Colômbia', 'México', 'Peru', 'Uruguai', 'Venezuela', 'Belize', 'Costa Rica', 'Estados Unidos', 'Guatemala', 'Honduras', 'Nicarágua', 'Bolívia'],
'moeda': ['Real', 'Peso argentino', 'Peso chileno', 'Peso colombiano', 'Peso mexicano', 
          'Sol peruano', 'Peso uruguaio', 'Bolívar soberano', 'Dólar de Belize', 'Colón costa-riquenho', 'Dólar dos Estados Unidos', 'Quetzal guatemalteco', 
           'Lempira hondurenho', 'Córdoba nicaraguense', 'Boliviano'],
'codigo': ['BRL', 'ARS', 'CLP', 'COP', 'MXN', 'PEN', 'UYU', 'VES', 'BZD', 'CRC', 'USD', 'GTQ', 'HNL', 'NIO', 'BOB']
}

currenciesdf = pd.DataFrame(currencies_todf)
currenciesdf.head(20)


# In[10]:


conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

for index, row in currenciesdf.iterrows():
    code = row['codigo']
    name = row['moeda']
    country = row['pais']
    datatype = 'currencies'
    dados = (code, name, country, datatype) 
    command = '''
        INSERT INTO currencies (currcode, currname, country, datatype)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM currencies 
            WHERE currcode = ? AND currname = ? AND country = ? AND datatype = ?
        )
    '''
    cursor.execute(command, dados + dados)
    conn.commit()
conn.close()


# In[11]:


conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

command = 'SELECT currcode FROM currencies'

cursor.execute(command)

# Recuperar os resultados da consulta
resultados = cursor.fetchall()

# Armazenar os valores da coluna em uma lista Python
coluna_lista = [row[0] for row in resultados]

# Exibir a lista
print(coluna_lista)


# In[12]:


for codeit in coluna_lista:
    codeit = codeit.lower()
    command = f'''
        CREATE TABLE IF NOT EXISTS {codeit}(
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            datatype TEXT NOT NULL
        );    
        '''
    cursor.execute(command)
    conn.commit()


# Fechar a conexão com o banco de dados
conn.close()


# In[ ]:





# In[13]:


conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

for currcode in coluna_lista:
    currcode = currcode.lower()
    command = f'SELECT MIN(date) FROM {currcode}'
    cursor.execute(command)
    lastdate = cursor.fetchall()
    lastdatetest = f'{lastdate}'
    lastdatetest = len(lastdatetest)
    if lastdatetest == 9: # GAMBIARRA MÁXIMA
        tenyragovar = tenyragodelta.strftime("%Y-%m-%d")
        todayvar = todaydelta.strftime("%Y-%m-%d")
        downloadv = yf.download(f"USD{currcode}=X", start=f"{tenyragovar}", end=f"{todayvar}")
        downloadv = downloadv.drop('Adj Close', axis=1)
        downloadv['datatype'] = 'currencies'
        downloadv['code'] = f'{currcode}'
        downloadv.reset_index(inplace=True)
        downloadv['Date'] = pd.to_datetime(downloadv['Date'])
        currcodel = currcode.lower()
        downloadv.to_sql(f'{currcodel}', conn, if_exists='append', index=False, dtype={'Date': 'DATE'})
        
    else:
        command = f'SELECT MAX(date) FROM {currcode}'
        cursor.execute(command)
        firstdate = cursor.fetchall()
        lastdatestr = lastdate[0][0].split()[0]
        lastdatedatetime = datetime.strptime(lastdatestr, '%Y-%m-%d')
        firstdatestr = firstdate[0][0].split()[0]
        firstdatedatetime = datetime.strptime(firstdatestr, '%Y-%m-%d')
        todayvar = todaydelta.strftime("%Y-%m-%d")
        firstdatestr = firstdatedatetime.strftime("%Y-%m-%d")
        print(firstdatedatetime)
        print(todaydelta)
        print(type(todaydelta))
        print(todayvar)
        print(firstdatestr)
        if firstdatestr == todaydelta:
            print('Up to date')
        else:
            downloadv = yf.download(f"USD{currcode}=X", start=f"{firstdatestr}", end=f"{todayvar}") # o Yahoo Finance só resgata os tickets de moeda depois do fechamento do dia. 
            # Rodar esse programa UMA VEZ POR DIA
            # PARA UMA ATUALIZAÇÃO: ADICIONAR UMA CHAVE DE "ATUALIZATION DATE"
            downloadv = downloadv.drop('Adj Close', axis=1)
            downloadv['datatype'] = 'currencies'
            downloadv['code'] = f'{currcode}'
            downloadv.reset_index(inplace=True)
            downloadv['Date'] = pd.to_datetime(downloadv['Date'])
            currcodel = currcode.lower()
            downloadv.to_sql(f'{currcodel}', conn, if_exists='replace', index=False, dtype={'Date': 'DATE'})
            print(downloadv)
            conn.commit()

conn.close()


# # Cripto

# In[14]:


### Cripto

cripto_df = pd.read_excel("cripto.xlsx")
print(cripto_df)



# In[15]:


def updatecripto(cripto):
    conn = sqlite3.connect('yfhistoric.db')
    cursor = conn.cursor()
    cripto = pd.DataFrame(cripto)
    for index, row in cripto.iterrows():
        code = row['criptocode']
        name = row['criptoname']
        datatype = 'criptocurrencies'
        dados = (code, name, datatype) 
        command = '''
            INSERT INTO cripto (criptocode, criptoname, datatype)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM cripto
                WHERE criptocode = ? AND criptoname = ? AND datatype = ?
            )
        '''
        cursor.execute(command, dados + dados)
        conn.commit()
    # SELECIONA TODOS OS CÓDIGOS DE TICKERS QUE VAMOS VER NO NOSSO DB
    command = 'SELECT criptocode FROM cripto'
    cursor.execute(command)
    
    
    # RECUPERA A CONSULTA EM UMA LISTA DE TUPLAS
    resultados = cursor.fetchall()
    # Armazenar os valores da coluna em uma lista Python comum
    coluna_lista = [row[0] for row in resultados]
    # CRIA UMA TABELA PARA CADA CÓDIGO
    for codeit in coluna_lista:
        codeit = codeit.lower()
        command = f'''
            CREATE TABLE IF NOT EXISTS "{codeit}"(
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                datatype TEXT NOT NULL
            );    
            '''
        cursor.execute(command)
        conn.commit()
       



    ############################## PREENCHER CADA TABELA COM O YAHOO FINANCE



    for commcode in coluna_lista: ### COMMCODE AQUI DEVERIA SER TICCODE
        attdate = datecheck(commcode)
        print(attdate)
        if attdate == "no att":
            print(f"Sem att para o ticker {commcode}")
        else:
            
            try:
                downloadv = yf.download(f"{commcode}", start=f"{attdate}", end=f"{todayvar}")
            except Exception as e:
                ex = f"{e}"
                download_errors.append(ex)
                print(f"O erro do código {commcode} foi {ex}")
            downloadv = downloadv.drop('Adj Close', axis=1)
            downloadv['datatype'] = 'cripto'
            downloadv['code'] = f'{commcode}'
            downloadv.reset_index(inplace=True)
            downloadv['Date'] = pd.to_datetime(downloadv['Date'])
            commcodel = commcode.lower()
            downloadv.to_sql(f'{commcodel}', conn, if_exists='replace', index=False, dtype={'Date': 'DATE'})
            conn.commit()
    conn.close()

############################ executando a função

updatecripto(cripto_df)


# # Commodities

# In[16]:


########################### commodities
commodities_todf = {
    'commodity': ['Ouro', 'Prata', 'Petróleo Crude (WTI)', 'Petróleo Brent Crude', 'Cobre', 'Gás Natural', 'Milho', 'Trigo', 'Café', 'Açúcar'],
    'codigo': ['GC=F', 'SI=F', 'CL=F', 'BZ=F', 'HG=F', 'NG=F', 'C=F', 'W=F', 'KC=F', 'SB=F']
}
commoditiesdf = pd.DataFrame(commodities_todf)


# In[17]:


conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

command = 'SELECT commcode FROM commodities'

cursor.execute(command)

# Recuperar os resultados da consulta
resultados = cursor.fetchall()

# Armazenar os valores da coluna em uma lista Python
coluna_lista = [row[0] for row in resultados]

# Exibir a lista
print(coluna_lista)


# In[18]:


def updatecommodities(dcticket):
    conn = sqlite3.connect('yfhistoric.db')
    cursor = conn.cursor()
    dcticketdf = pd.DataFrame(dcticket)
    for index, row in dcticketdf.iterrows():
        code = row['codigo']
        name = row['commodity']
        datatype = 'commodities'
        dados = (code, name, datatype) 
        command = '''
            INSERT INTO commodities (commcode, comname, datatype)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM commodities
                WHERE commcode = ? AND comname = ? AND datatype = ?
            )
        '''
        cursor.execute(command, dados + dados)
        conn.commit()
    # SELECIONA TODOS OS CÓDIGOS DE TICKERS QUE VAMOS VER NO NOSSO DB
    command = 'SELECT commcode FROM commodities'
    cursor.execute(command)
    
    
    # RECUPERA A CONSULTA EM UMA LISTA DE TUPLAS
    resultados = cursor.fetchall()
    # Armazenar os valores da coluna em uma lista Python comum
    coluna_lista = [row[0] for row in resultados]
    # CRIA UMA TABELA PARA CADA CÓDIGO
    for codeit in coluna_lista:
        codeit = codeit.lower()
        command = f'''
            CREATE TABLE IF NOT EXISTS "{codeit}"(
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                datatype TEXT NOT NULL
            );    
            '''
        cursor.execute(command)
        conn.commit()
       



    ############################## PREENCHER CADA TABELA COM O YAHOO FINANCE



    for commcode in coluna_lista: ### COMMCODE AQUI DEVERIA SER TICCODE
        attdate = datecheck(commcode)
        print(attdate)
        if attdate == "no att":
            print(f"Sem att para o ticker {commcode}")
        else:
            
            try:
                downloadv = yf.download(f"{commcode}", start=f"{attdate}", end=f"{todayvar}")
            except Exception as e:
                ex = f"{e}"
                download_errors.append(ex)
                print(f"O erro do código {commcode} foi {ex}")
            downloadv = downloadv.drop('Adj Close', axis=1)
            downloadv['datatype'] = 'commodities'
            downloadv['code'] = f'{commcode}'
            downloadv.reset_index(inplace=True)
            downloadv['Date'] = pd.to_datetime(downloadv['Date'])
            commcodel = commcode.lower()
            downloadv.to_sql(f'{commcodel}', conn, if_exists='replace', index=False, dtype={'Date': 'DATE'})
            conn.commit()
    conn.close()

updatecommodities(commoditiesdf)


# # Tickets
# 
# >Estava com problemas para fazer a função if de consulta da última data de atualização e diversas formas de fazer o download para não sobrecarregar o Yahoo Finance, mas parece que o yf é robusto
# >e fazer download de 10 anos dos tickers não vai ser problema. Mas é algo a ser otimizado. Uma forma é fazer uma subtração do lastdate. Pra frente veremos.
# >O mesmo vale para as saídas de erro com tickers com código incorreto, isso depende dos ajustes que tem que ser feitos com o código pronto.

# In[19]:


###### CRIAÇÃO E MANUTENÇÃO DIRETÓRIO TICKERS ####

# Nome da pasta que você deseja verificar/criar
nome_pasta = "tickets"
# Verificar se o diretório existe
if not os.path.exists(nome_pasta):
    # Se não existir, criar o diretório
    os.makedirs(nome_pasta)
    
# Diretório onde estão os arquivos Excel
diretorio_tickets = "tickets"

# Lista para armazenar os dataframes
tickets = []

# Verificar se o diretório existe
if os.path.exists(diretorio_tickets):
    # Listar todos os arquivos na pasta
    arquivos_excel = [arquivo for arquivo in os.listdir(diretorio_tickets) if arquivo.endswith('.xlsx')] # LISTA TODOS OS 
    
    # Ler cada arquivo Excel e adicionar o dataframe à lista
    for arquivo in arquivos_excel:
        caminho_arquivo = os.path.join(diretorio_tickets, arquivo)
        df = pd.read_excel(caminho_arquivo)
        tickets.append(df) # UMA LISTA DE DATFRAMES
else:
    print(f"O diretório '{diretorio_tickets}' não existe.")


# In[20]:


download_errors = []

caminho_arquivo_e = f"tickererrors_{today}.txt"
caminho_arquivo_e = os.path.join(rootdire, caminho_arquivo_e)

def updateticket(dcticket):
    conn = sqlite3.connect('yfhistoric.db')
    cursor = conn.cursor()
    dcticketdf = pd.DataFrame(dcticket)
    for index, row in dcticketdf.iterrows():
        code = row['codigo']
        name = row['empresa']
        country = row['pais']
        niche = row['nicho']
        datatype = 'tickets'
        dados = (code, name, datatype, niche, country) 
        command = '''
            INSERT INTO tickets (ticcode, ticname, datatype, ticcat, country)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM tickets
                WHERE ticcode = ? AND ticname = ? AND datatype = ? AND ticcat = ? AND country = ?
            )
        '''
        cursor.execute(command, dados + dados)
        conn.commit()
    # SELECIONA TODOS OS CÓDIGOS DE TICKERS QUE VAMOS VER NO NOSSO DB
    command = 'SELECT ticcode FROM tickets'
    cursor.execute(command)
    
    
    # RECUPERA A CONSULTA EM UMA LISTA DE TUPLAS
    resultados = cursor.fetchall()
    # Armazenar os valores da coluna em uma lista Python comum
    coluna_lista = [row[0] for row in resultados]
    # CRIA UMA TABELA PARA CADA CÓDIGO
    for codeit in coluna_lista:
        codeit = codeit.lower()
        command = f'''
            CREATE TABLE IF NOT EXISTS "{codeit}"(
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                datatype TEXT NOT NULL
            );    
            '''
        cursor.execute(command)
        conn.commit()
       



    ############################## PREENCHER CADA TABELA COM O YAHOO FINANCE



    for commcode in coluna_lista: ### COMMCODE AQUI DEVERIA SER TICCODE
        attdate = datecheck(commcode)
        print(attdate)
        if attdate == "no att":
            print(f"Sem att para o ticker {commcode}")
        else:
            
            try:
                downloadv = yf.download(f"{commcode}", start=f"{attdate}", end=f"{todayvar}")
            except Exception as e:
                ex = f"{e}"
                download_errors.append(ex)
                print(f"O erro do código {commcode} foi {ex}")
            downloadv = downloadv.drop('Adj Close', axis=1)
            downloadv['datatype'] = 'tickets'
            downloadv['code'] = f'{commcode}'
            downloadv.reset_index(inplace=True)
            downloadv['Date'] = pd.to_datetime(downloadv['Date'])
            commcodel = commcode.lower()
            downloadv.to_sql(f'{commcodel}', conn, if_exists='replace', index=False, dtype={'Date': 'DATE'})
            conn.commit()
    conn.close()

# Abrir o arquivo no modo de escrita
with open(caminho_arquivo_e, 'wb') as arquivo:
    # Escrever cada elemento da lista em uma nova linha do arquivo
    for elemento in download_errors:
        
        arquivo.write('%s\n' % elemento)

############################ executando a função

for tic in tickets:
    updateticket(tic)


# In[21]:


#################### TABELA COUNTRIES

## AQUI A TABELA COUNTRIES REGISTRA TODOS OS PAÍSES TRATADOS ATÉ O MOMENTO
conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%country%'")
tables = cursor.fetchall()
tables = [tupla[0] for tupla in tables]

print(tables)

for tab in tables:
    print(tab)
    command = f''' 
            INSERT INTO countries (country)
            SELECT DISTINCT country FROM {tab}
            WHERE NOT EXISTS (
                SELECT 1 FROM countries WHERE country = {tab}.country 
            )
            '''
  
    cursor.execute(command)
    conn.commit()
    


latam = ['Argentina', 'Bolívia', 'Brasil', 'Chile', 'Colômbia', 'Costa Rica', 'Cuba', 'Equador',
        'El Salvador', 'Guiana', 'Guatemala', 'Haiti', 'Honduras', 'México',
        'Nicarágua', 'Panamá', 'Paraguai', 'Peru', 'República Dominicana', 'Suriname', 
        'Uruguai', 'Venezuela', 'Belize'] # O CONCEITO DE AMÉRICA LATINA AQUI É EXPANDIDO. SÃO TODOS PAÍSES PRA BAIXO DO RIO BRAVO, INCLUINDO CARIBE.



command = "SELECT country FROM countries"
cursor.execute(command)
countriesvar = cursor.fetchall()
countriesvar = [tupla[0] for tupla in countriesvar]

countriesvar = pd.DataFrame(countriesvar, columns = ['country'])

# Cria um novo dataframe com os países adicionais
new_countries_df = pd.DataFrame({'country': latam})

# Adiciona os novos países ao dataframe existente
countriesvar = countriesvar.append(new_countries_df, ignore_index=True)

# Remove duplicatas, se houver
countriesvar = countriesvar.drop_duplicates().reset_index(drop=True)


print(countriesvar)


countriesvar['latam'] = ['Latam' if country in latam else 'Not Latam' for country in countriesvar['country']]

countriesvar.to_sql('countries', conn, if_exists='replace', index=False)


alpha3code = pd.read_excel('alpha.xlsx') # IMPORTANTE: SE FAZ NECESSÁRIO UM ARQUIVO COM UMA LISTA DE ALPHA3 CODE PARA CONSULTA DE AGREGADOS


countriesvar = pd.merge(countriesvar, alpha3code, on='country', how='left')
countriesvar.to_sql('countries', conn, if_exists='replace', index=False)

conn.close()


# # AGREGADOS

# Os dados são extraidos através da API do World Bank. Eles tem pesos diferentes.
# 
# O PIB é o Produto Interno Bruto em dólares americanos (USD). Não é ajustado pela inflação
# PIB/capta é em USD, normal.
# POPCRESC é a porcentagem de crescimento da população desse país. 
# TXIFLA é a porcentagem de crescimento da inflação
# DIVPUB é a porcentagem do PIB que um país tem como dívida pública
# 

# In[22]:


############## AGREGADOS
conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

# Regatar alpha3code que é o código ISO9001 padrão mundial para referir-se aos países.
command = "SELECT alpha3code FROM countries"
cursor.execute(command)
alpha3cod = cursor.fetchall()
alpha3cod = [tupla[0] for tupla in alpha3cod]

# Insere/atualiza os códigos dos agregados no World Bank
agrcodes = pd.read_excel('pandas_datareaderagregates.xlsx')
agrcodes.to_sql('agregates', conn, if_exists='replace', index=False)

agrcodes = sqltodf('agregates')

print(agrcodes)


# In[23]:


# Sistema de data e tipos de variáveis
todayyear = datetime.today()
tenyearsago = todayyear - timedelta(365 * 10)
todayyear = todayyear.strftime("%Y")
tenyearsago = tenyearsago.strftime("%Y")
todayyear = f'{todayyear}'
tenyearsago = f'{tenyearsago}'

# Reorganização Alpha 3 Codes 
alpha3cod = list(filter(lambda x: x is not None, alpha3cod))




for index, row in agrcodes.iterrows():
    name2 = row['agrcode']
    name2 = f'{name2}'
    print(name2)
    agr = row['agrcodewb']
    for alp in alpha3cod:
        data = wbdata.get_data(agr, country=alp, date=(tenyearsago, todayyear))
        data = pd.DataFrame(data)
        data['datatype'] = 'agregates'
        data['agrcode'] = name2
        name = f"{alp}_WB_{name2}"
        name = name.replace(".", "_") # Dando problema na consulta e preenchimento do country acima no BD SQL
        name = f'{name}'
        drop = ['indicator', 'country', 'obs_status', 'unit', 'decimal']
        data = data.drop(columns=drop, inplace=False)
        data.rename(columns={'countryiso3code': 'iso3code'}, inplace=True)
        print(data)
        conn = sqlite3.connect('yfhistoric.db')
        cursor = conn.cursor()
        data.to_sql(name, conn, if_exists='replace', index=False)
    conn.close()

    
conn.close()


# # Projeções
# ## 

# Aqui vamos fazer as projeções diárias e projeções aproveitando os dados coletados.
# 
# ### PROJEÇÕES DIÁRIAS:
# + Variação do High e Low
# + Tendência de um ticker em curto-prazo (definir posteriormente)
# 
# ### PROJEÇÕES PERMANENTES
# + PIB dos países exportadores de petróleo vs empresas de petróleo a nível mundial ou local
# + Preço do petróleo nas duas formas vs PIB dos petroleiros
# + Mesma lógica pra outras commodities
# + Commodities em geral vs PIB da América Latina em geral. vs Inflação, desemprego, etc

# In[24]:


conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS mlearning(
        id INTEGER PRIMARY KEY,
        model TEXT NOT NULL,
        dataorigin TEXT NOT NULL, 
        period DATE,
        country TEXT NOT NULL,
        datatype TEXT NOT NULL,
        FOREIGN KEY (datatype) REFERENCES text(datatype)
        FOREIGN KEY (country) REFERENCES countries(country)
    );    
    ''') 
# dataorigin é o código do ticker, moeda, commoditie etc. 
# period é a data inicial e final da análise. 
# model é o modelo de previsão


conn.close()


# In[25]:


def showsql(sqltable):
    df = sqltodf(f'{sqltable}')
    print(df)


# In[26]:


showsql('commodities')


# In[27]:


showsql('"bz=f"')


# In[28]:


df = sqltodf('tickets')
niche = df['ticcat'].unique() 
print(niche)


# In[29]:


# Todas as empresas petroliferas ('Petróleo e gás', 'Petróleo e Gás', 'Petroquímica')

conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()
cursor.execute('''
SELECT ticcode
FROM tickets
WHERE ticcat IN ('Petróleo e gás', 'Petróleo e Gás', 'Petroquímica');

    ''') 
petroleo = cursor.fetchall()
petroleo = [row[0] for row in petroleo]
print(petroleo)

conn.close()


# In[30]:


# CORRELAÇÃO ENTRE O PIB DOS PAÍSES PRODUTORES DE PETRÓLEO E A MÉDIA ANUAL DO PREÇO DO PETRÓLEO

'''sqltodf('''


# # News e Texts
# #### Para essa parte é necessário um processo de Scrapping das páginas dos principais jornais de cada país. A parte complicada é essa. Como exemplo eu produzi um scrapping de 4 páginas, 3 do Brasil e uma da Argentina. O que é complicado é encontrar a secção nos códigos fonte HTML onde você encontra as headlines, normalmente os jornais "mudam de padrão" dessa informação para não ser tão fácil "raspar" a página através apenas da página inicial. Isso significa que o trabalho é passar de página em página e identificar os 35 box de headlines nos sites escolhidos ('news_source.xlsx'). Uma alternativa que tive em mente é um algoritimo de linguagem natural (NLP) pra encontrar a headline ou uma LLM comum que analise o HTML inteiro para tal. Para a LLM analisando o código inteiro a limitação é a quantidade de tokens de processamento que torna impossível "em uma tacada só" e não sei se teremos efetividade se "desmembrarmos" o código, fora o tempo de processamento porque são, no exemplo da Folha de São Paulo, 400.000 tokens. 12,000 linhas de HTML. 
# #### Vou construir manualmente por enquanto, mas é um processo que com certeza pode ser automatizado com algum tipo de ferramenta da área de IA.
# 
# #### Para a produção dos resumos duas opções foram cogitadas: o Gemini que é rápido e fácil, mas limitado. A outra opção é rodar alguma LLM localmente através de uma biblioteca ou programa mesmo. Os problemas que isso gera são: custo de processamento; possível imprecisão pelo fato das LLMs rodando localmente serem menos potentes; demora na produção. A vantagem possível é futuramente fazer um "fine tuning" para que a LLM se adeque à tarefa. 
# #### Pelo fato de que as notícias podem conter conteúdo "nocivo" e o Gemini não processar algumas, vamos optar primeiramente pelo LLM Studio que é simples e rápido. 

# In[31]:


####### Sites que foram pensados

newspaperDF = pd.read_excel('news_source.xlsx')
newspaperDF.head(40)


# In[32]:


######### SQL manual para armazenar os textos

conn = sqlite3.connect('yfhistoric.db')
cursor = conn.cursor()

for index, row in newspaperDF.iterrows():
    code = row['mainlink']
    name = row['newspaper']
    country = row['country']
    datatype = 'news'
    dados = (code, name, country, datatype) 
    command = '''
        INSERT INTO news (newspaperlink , newspapername, country, datatype)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM news
            WHERE newspapername = ? AND newspaperlink = ? AND country = ? AND datatype = ?
        )
    '''
    cursor.execute(command, dados + dados)
    conn.commit()
conn.close()



# In[33]:


# OPÇÃO 1: LLM STUDIO
def llmstudio(noticia):
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

    completion = client.chat.completions.create(
      model="local-model", # this field is currently unused
      messages=[
        {"role": "system", "content": "Você agora é um jornalista preocupado em resumir notícias. A forma com que você escreverá é como se estivesse escrevendo essa notícia em um site. Você está escrevendo para um resumo geral de notícias que aparecerá em uma pequena caixa em um site. Você resumirá a notícia em no máximo 500 caracteres e 3 parágrafos."},
        {"role": "user", "content": f"Resuma em português a seguinte notícia em aproximadamente 500 caracteres e 3 parágrafos:{noticia}"}
      ],
      temperature=0.5,
      timeout = 999  
    )

    texto = completion.choices[0].message
    # Acessando o texto da mensagem
    texto_noticia = texto.content
    return texto_noticia
    
# OPÇÃO 2: SUMARRIZER DO HUGGINFACE (APENAS EM PT-PT)


def ptt5(text):
    token_name = 'unicamp-dl/ptt5-base-portuguese-vocab'
    model_name = 'phpaiola/ptt5-base-summ-xlsum'

    tokenizer = T5Tokenizer.from_pretrained(token_name )
    model_pt = T5ForConditionalGeneration.from_pretrained(model_name)
    inputs = tokenizer.encode(text, max_length=9999, truncation=True, return_tensors='pt')
    summary_ids = model_pt.generate(inputs, max_length=700, min_length=300, num_beams=3, no_repeat_ngram_size=3, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0])
    return summary


# In[34]:


# Tradutor para línguas diferentes do português. O SUMMARIZADOR SÓ RESUME EM PORTUGUÊS!!!

def to_pt(text):
    translator = Translator()
    translated_text = translator.translate(text, dest='pt')
    return translated_text.text



# In[35]:


# Por uma questão de visualização e redundancia, vamos utilizar o próprio sistema também para armazenar os "sumários" e "notícias cruas"

foldersumtext = "text_summaries"
text_summaries = os.path.join(rootdire, foldersumtext)
todaytsfolder = os.path.join(text_summaries, today)
if os.path.exists(text_summaries):
    todaytsfolder = os.path.join(text_summaries, today)
    print(f"trying {todaytsfolder}")
    if os.path.exists(todaytsfolder):
          print("Todays folder for texts and summaries already exists")
    else:
          try:
              os.mkdir(todaytsfolder)
              print("Making diretory")
          except Exception as e:
              print(e)
else:      
    try:
            os.mkdir(text_summaries)
            os.mkdir(todaytsfolder)
            print(f"Making diretory {todaysfolder}")
    except Exception as e:
              print(e)      
          
              


# In[36]:


# Função para pegar as notícias, sumarizar, traduzir se necessário
def newsatt(journal_url, country, journal_name, arg):
    # Fazendo uma solicitação HTTP para obter o conteúdo da página inicial do jornal
    response = requests.get(journal_url)
    response.raise_for_status()  # Verificar se a solicitação foi bem-sucedida

    # Criando um objeto BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    arg = f'''arg'''
    exec(arg)

    headline_text = {}
    summaries = {}
    print(headlines)
    # Acessando os links e obtendo o texto de cada manchete
    for headline in headlines:
        link = headline['href']  # Obtendo o link da manchete

        # Adicionando '12ft.io/' ao link para contornar o paywall
        link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

        # Inicializando o objeto Article da biblioteca newspaper3k
        article = newspaper.Article(link)

        # Baixando e parseando o conteúdo da manchete
        article.download()
        article.parse()

        # Obtendo o texto da manchete
        hlarticle = article.text.strip()
        headline_text[headline] = hlarticle
        if country != "Brasil":
            headline_text[headline] = to_pt(headline_text[headline])
        else:
            pass
        summary = ptt5(headline_text[headline])
        summaries[headline] = summary 
        print(headline_text[headline])
        print('*' * 50) 
        print(summary)
        print('!' * 500)
        name = link.replace("/", "_")
        name = name.replace("https://webcache.googleusercontent.com/search?q=cache:https:__www1.folha.uol.com.br_", " ")
        name = name.strip()
        country = country.lower()
        mother_folder = os.path.join(todaytsfolder, country)
        os.makedirs(mother_folder)
        journal_name = journal_name.lower()
        mother_folder = os.path.join(mother_folder, journal_name)
        os.makedirs(mother_folder)
        print(f"@@@@@@@@ {name} @@@@@@@@@@@@@")
        caminho_arquivo = f'{name}.txt' 
        caminho_arquivo = os.path.join(mother_folder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(headline_text[headline])

        caminho_arquivo = f'sum_{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(summary)


# In[ ]:





# In[37]:


news_source = pd.read_excel("news_source_arg.xlsx")

news_source.head(4)


# In[38]:


teste = '''for index, rows in news_source.iterrows(): #journal_url, country, journal_name, argument
    country = rows['country']
    journal_name = rows['newspaper']
    journal_url = rows['mainlink']
    arg = rows['arg']
    print(f" ############## Tentando {journal_name}") 
    newsatt(journal_url, country, journal_name, arg)'''


# In[40]:


##### Folha de São Paulo

journal_url = 'https://www1.folha.uol.com.br/'

# Fazendo uma solicitação HTTP para obter o conteúdo da página inicial do jornal
response = requests.get(journal_url)
response.raise_for_status()  # Verificar se a solicitação foi bem-sucedida

# Criando um objeto BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Encontrando as manchetes
headlines = soup.select('.c-rotate-headlines__link')[:3]  # Extrai os três primeiros links das manchetes ####### A PARTE DIFÍCIL ESTÁ AQUI

headline_text = {}
summaries = {}

# Acessando os links e obtendo o texto de cada manchete
for headline in headlines:
    link = headline['href']  # Obtendo o link da manchete
    
    # Adicionando '12ft.io/' ao link para contornar o paywall
    link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

    # Inicializando o objeto Article da biblioteca newspaper3k
    article = newspaper.Article(link)

    # Baixando e parseando o conteúdo da manchete
    article.download()
    article.parse()

    # Obtendo o texto da manchete
    hlarticle = article.text.strip()
    headline_text[headline] = hlarticle
    summary = ptt5(headline_text[headline])
    summaries[headline] = summary 
    print(headline_text[headline])
    print('*' * 50) 
    print(summary)
    print('!' * 500)
    name = link.replace("/", "_")
    name = name.replace("https://webcache.googleusercontent.com/search?q=cache:https:__www1.folha.uol.com.br_", " ")
    name = name.replace("https:__webcache.googleusercontent.com_search?q=cache:https:__f5.folha.uol.com.br", " ")
    name = name.replace("https:__webcache.googleusercontent.com_search?q=cache:", " ")
    name = name.strip()
    print(f"@@@@@@@@ {name} @@@@@@@@@@@@@")
    caminho_arquivo = f'{name}.txt' 
    caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
    with open(caminho_arquivo, "w") as arquivo:
    # Escrever o texto no arquivo
        arquivo.write(headline_text[headline])
    
    caminho_arquivo = f'sum_{name}.txt'
    caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
    with open(caminho_arquivo, "w") as arquivo:
    # Escrever o texto no arquivo
        arquivo.write(summary)


# In[41]:


##### estadão

journal_url = 'https://www.estadao.com.br/'

# Fazendo uma solicitação HTTP para obter o conteúdo da página inicial do jornal
response = requests.get(journal_url)
response.raise_for_status()  # Verificar se a solicitação foi bem-sucedida

# Criando um objeto BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Encontrando a parte do HTML que contém as manchetes
headline_section = soup.find('div', class_='noticia-content-block')

        # Verificando se a seção de manchetes foi encontrada
if headline_section:
            # Extrair os links das manchetes
    headlines = headline_section.find_all('a')[:3]  # Extrai os três primeiros links das manchetes

    headlines_text = []

            # Acessando os links e obtendo o texto de cada manchete
    for headline in headlines:
        link = headline['href']  # Obtendo o link da manchete
                
                # Adicionando '12ft.io/' ao link para contornar o paywall
        link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

        # Inicializando o objeto Article da biblioteca newspaper3k
        article = newspaper.Article(link)

        # Baixando e parseando o conteúdo da manchete
        article.download()
        article.parse()

                
        hlarticle = article.text.strip()
        headline_text[headline] = hlarticle
        summary = ptt5(headline_text[headline])
        summaries[headline] = summary 
        print(headline_text[headline])
        print('*' * 50) 
        print(summary)
        print('!' * 500)
        name = link.replace("/", "_")
        name = name.replace("https:__webcache.googleusercontent.com_search?q=cache:https:__www.estadao.com.br_", " ")
        name = name.strip()
     
        print(f"@@@@@@@@ {name} @@@@@@@@@@@@@")
        caminho_arquivo = f'{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(headline_text[headline])

        caminho_arquivo = f'sum_{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(summary)
else: 
    print('error')


# In[42]:


##### UOL

journal_url = 'https://economia.uol.com.br/'

# Fazendo uma solicitação HTTP para obter o conteúdo da página inicial do jornal
response = requests.get(journal_url)
response.raise_for_status()  # Verificar se a solicitação foi bem-sucedida

# Criando um objeto BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Encontrando a parte do HTML que contém as manchetes
headline_section = soup.find('div', class_='row')

        # Verificando se a seção de manchetes foi encontrada
if headline_section:
            # Extrair os links das manchetes
    headlines = headline_section.find_all('a')[:3]  # Extrai os três primeiros links das manchetes

    headlines_text = []

            # Acessando os links e obtendo o texto de cada manchete
    for headline in headlines:
        link = headline['href']  # Obtendo o link da manchete
                
                # Adicionando '12ft.io/' ao link para contornar o paywall
        link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

        # Inicializando o objeto Article da biblioteca newspaper3k
        article = newspaper.Article(link)

        # Baixando e parseando o conteúdo da manchete
        article.download()
        article.parse()

                
        hlarticle = article.text.strip()
        headline_text[headline] = hlarticle
        summary = ptt5(headline_text[headline])
        summaries[headline] = summary 
        print(headline_text[headline])
        print('*' * 50) 
        print(summary)
        print('!' * 500)
        name = link.replace("/", "_")
        name = name.replace("https:__webcache.googleusercontent.com_search?q=cache:https:__economia.uol.com.br_", " ")
        name = name.strip()
        print(f"@@@@@@@@ {name} @@@@@@@@@@@@@")
        caminho_arquivo = f'{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(headline_text[headline])
        caminho_arquivo = f'sum_{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(summary)
else: 
    print('error')
       


# In[43]:


##### Clarín

journal_url = 'https://www.clarin.com/'

# Fazendo uma solicitação HTTP para obter o conteúdo da página inicial do jornal
response = requests.get(journal_url)
response.raise_for_status()  # Verificar se a solicitação foi bem-sucedida


# Criando um objeto BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Encontrando a parte do HTML que contém as manchetes
attribute = 'data-mrf-recirculation'
headline_section = soup.find(attrs={attribute: True})

headlines = headline_section.find_all('a')[:3]
        # Verificando se a seção de manchetes foi encontrada
if headline_section:
            # Extrair os links das manchetes
    headlines = headline_section.find_all('a')[:3]  # Extrai os três primeiros links das manchetes

    headlines_text = []

            # Acessando os links e obtendo o texto de cada manchete
    for headline in headlines:
        link = headline['href']  # Obtendo o link da manchete
                
                # Adicionando '12ft.io/' ao link para contornar o paywall
        link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

        # Inicializando o objeto Article da biblioteca newspaper3k
        article = newspaper.Article(link)

        # Baixando e parseando o conteúdo da manchete
        article.download()
        article.parse()

                
        hlarticle = article.text.strip()
        headline_text[headline] = hlarticle
        headline_text[headline] = to_pt(headline_text[headline])
        summary = ptt5(headline_text[headline])
        summaries[headline] = summary 
        print(headline_text[headline])
        print('*' * 50) 
        print(summary)
        print('!' * 500)
        name = link.replace("/", "_")
        name = name.replace("https:__webcache.googleusercontent.com_search?q=cache:https:__www.clarin.com_", " ")
        name = name.strip()
        print(f"@@@@@@@@ {name} @@@@@@@@@@@@@")
        caminho_arquivo = f'{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(headline_text[headline])

        caminho_arquivo = f'sum_{name}.txt'
        caminho_arquivo = os.path.join(todaytsfolder, caminho_arquivo)
        with open(caminho_arquivo, "w") as arquivo:
        # Escrever o texto no arquivo
            arquivo.write(summary)
else: 
    print('error')
       


# # PROTO CÓDIGO DOS TICKETS
# 

# In[ ]:


'''
empresasbr = {
    'empresa': ['Vale', 'Itaú Unibanco', 'Bradesco', 'Ambev', 'Banco do Brasil', 'B3', 'Petrobras', 'Cielo', 'Eletrobras', 'Magazine Luiza',
                'Votorantim', 'Gerdau', 'Rumo', 'Cyrela', 'Klabin', 'Randon', 'Ultrapar', 'Usiminas', 'Lojas Americanas', 'Suzano',
                'Fleury', 'Gol', 'Santander Brasil', 'Localiza', 'Ecorodovias', 'Braskem', 'WEG', 'JBS', 'IRB Brasil', 'CCR'],
    'codigo': ['VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'BBAS3.SA', 'B3SA3.SA', 'PETR4.SA', 'CIEL3.SA', 'ELET6.SA', 'MGLU3.SA',
                'VVAR3.SA', 'GGBR4.SA', 'RAIL3.SA', 'CYRE3.SA', 'KLBN11.SA', 'RAPT4.SA', 'UGPA3.SA', 'USIM5.SA', 'LAME4.SA', 'SUZB3.SA',
                'FLRY3.SA', 'GOLL4.SA', 'SANB11.SA', 'RENT3.SA', 'ECOR3.SA', 'BRKM5.SA', 'WEGE3.SA', 'JBSS3.SA', 'IRBR3.SA', 'CCRO3.SA'],
    'pais': ['Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil',
              'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil', 'Brasil'],
    'nicho': ['Mineração', 'Serviços Financeiros', 'Serviços Financeiros', 'Bebidas', 'Serviços Financeiros', 'Serviços Financeiros', 'Petróleo e Gás', 'Tecnologia Financeira', 'Energia', 'Varejo',
              'Diversificado', 'Metalurgia', 'Logística', 'Construção Civil', 'Papel e Celulose', 'Automotivo', 'Diversificado', 'Metalurgia', 'Varejo', 'Papel e Celulose',
              'Saúde', 'Transporte Aéreo', 'Serviços Financeiros', 'Aluguel de Carros', 'Infraestrutura', 'Petroquímica', 'Energia', 'Alimentício', 'Seguros', 'Infraestrutura']
}

empresasar = {
    'empresa': ['YPF', 'Grupo Financiero Galicia', 'Banco Macro', 'MercadoLibre', 'Telecom Argentina', 'BBVA Banco Francés', 'Cresud', 'Pampa Energía', 'Tenaris', 'Globant',
                'Banco de la Nación Argentina', 'Ternium', 'Central Puerto', 'Banco Santander Río', 'Grupo Supervielle', 'YPF Luz', 'Banco BBVA Argentina', 'Transportadora de Gas del Sur', 'Despegar.com', 'Banco de Galicia y Buenos Aires',
                'Aluar Aluminio', 'Molinos Río de la Plata', 'Edenor', 'IRSA Propiedades Comerciales', 'Banco Patagonia', 'Telefónica de Argentina', 'Siderar', 'Consultatio', 'Molinos Agro', 'TGS'],
    'codigo': ['YPFD.BA', 'GGAL.BA', 'BMA.BA', 'MELI.BA', 'TECO2.BA', 'BBAR.BA', 'CRES.BA', 'PAMP.BA', 'TS.BA', 'GLOB.BA',
               'BMA.BA', 'TXAR.BA', 'CEPU.BA', 'RIO.BA', 'SUPV.BA', 'YPFL.BA', 'BBVA.BA', 'TGSU2.BA', 'DESP.BA', 'GGAL.BA',
               'ALUA.BA', 'MOLI.BA', 'EDN.BA', 'IRSA.BA', 'BPAT.BA', 'TECO2.BA', 'ERAR.BA', 'CTIO.BA', 'MOLA.BA', 'TGSU2.BA'],
    'pais': ['Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina',
             'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina',
             'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina', 'Argentina'],
    'nicho': ['Petróleo e Gás', 'Serviços Financeiros', 'Serviços Financeiros', 'Tecnologia', 'Telecomunicações', 'Serviços Financeiros', 'Agricultura', 'Energia', 'Metalurgia', 'Tecnologia',
              'Serviços Financeiros', 'Metalurgia', 'Energia', 'Serviços Financeiros', 'Serviços Financeiros', 'Petróleo e Gás', 'Serviços Financeiros', 'Petróleo e Gás', 'Tecnologia', 'Serviços Financeiros',
              'Metalurgia', 'Alimentício', 'Energia', 'Imobiliário', 'Serviços Financeiros', 'Telecomunicações', 'Metalurgia', 'Consultoria', 'Alimentício', 'Energia']
}

empresasmex = {
    'empresa': ['América Móvil', 'Grupo México', 'FEMSA', 'Grupo Bimbo', 'Cemex', 'Grupo Financiero Banorte', 'Grupo Elektra', 'Gruma', 'Grupo Aeroportuario del Pacífico', 'Alfa', 
                'Grupo Aeroportuario del Centro Norte', 'Grupo Carso', 'Genomma Lab Internacional', 'Grupo Aeroportuario del Sureste', 'Grupo Aeroportuario de la Ciudad de México', 
                'Grupo Simec', 'Alpek', 'Controladora Vuela Compañía de Aviación', 'Gentera', 'Banco Santander México', 'Televisa', 'Grupo Lala', 'Grupo Herdez', 
                'Grupo Cementos de Chihuahua', 'Grupo Gigante', 'Banco del Bajío', 'Grupo Sanborns', 'Fibra Uno', 'Grupo Industrial Maseca', 'Grupo Kuo'],
    'codigo': ['AMXL.MX', 'GMEXICOB.MX', 'FEMSAUBD.MX', 'BIMBOA.MX', 'CEMEXCPO.MX', 'GFNORTEO.MX', 'ELEKTRA.MX', 'GRUMAB.MX', 'GAPB.MX', 'ALFAA.MX', 
                'OMAB.MX', 'GCARSOA1.MX', 'LABB.MX', 'ASURB.MX', 'GACMAB.MX', 'SIMECB.MX', 'ALPEKA.MX', 'VLRS.MX', 'GENTERA.MX', 'BSMXB.MX', 'TLEVISACPO.MX', 
                'LALAB.MX', 'HERDEZ.MX', 'GCC.MX', 'GIGANTE.MX', 'BBAJIOO.MX', 'GSANBORB-1.MX', 'FUNO11.MX', 'GRUMAB.MX', 'KUOB.MX'],
    'pais': ['México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 
             'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México', 'México'],
    'nicho': ['Telecomunicações', 'Mineração', 'Bebidas', 'Alimentício', 'Construção', 'Serviços Financeiros', 'Varejo', 'Alimentício', 'Transporte', 'Conglomerado',
              'Transporte', 'Conglomerado', 'Farmacêutico', 'Transporte', 'Transporte', 'Metalurgia', 'Químico', 'Transporte', 'Serviços Financeiros', 'Serviços Financeiros', 'Mídia',
              'Alimentício', 'Alimentício', 'Construção', 'Varejo', 'Serviços Financeiros', 'Varejo', 'Imobiliário', 'Indústria', 'Conglomerado']
}

empresascol = {
    'empresa': ['Ecopetrol', 'Grupo Aval', 'Bancolombia', 'Grupo Nutresa', 'Grupo Argos', 'Cementos Argos', 'Grupo Sura', 'Grupo Éxito', 'ISA', 'Banco de Bogotá',
                'Grupo Bolívar', 'Grupo EPM', 'Almacenes Éxito', 'Terpel', 'Celsia', 'Bancolombia Preferencial', 'Davivienda', 'Grupo Energía Bogotá', 'Cementos Argos Preferencial', 'Grupo Nutresa Preferencial',
                'Grupo Argos Preferencial', 'Grupo Aval Preferencial', 'Corficolombiana', 'ISA Preferencial', 'Banco de Bogotá Preferencial', 'Banco de Occidente', 'Grupo Sura Preferencial', 'Grupo Éxito Preferencial', 'Cemex Latam Holdings', 'ISA Pref A'],
    'codigo': ['ECOPETL.BO', 'AVAL.BO', 'CIB.BO', 'NUTRESA.BO', 'GRUPOARG.BO', 'CEMARGOS.BO', 'GRUPOSURA.BO', 'EXITO.BO', 'ISA.BO', 'BOGOTA.BO',
               'BOLIVAR.BO', 'EPM.BO', 'EXITO.BO', 'TERPEL.BO', 'CELSIA.BO', 'BCOLOMBIA.BO', 'PFDAVVNDA.BO', 'EEB.BO', 'CARTGENA.BO', 'NUTRESA.BO',
               'GRUPOARG.BO', 'AVAL.BO', 'COLFIC.BO', 'ISA.BO', 'BOGOTA.BO', 'OCCIDENTE.BO', 'GRUPOSURA.BO', 'EXITO.BO', 'CLH.BO', 'ISA.BO'],
    'pais': ['Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia',
             'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia',
             'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia', 'Colômbia'],
    'nicho': ['Petróleo e Gás', 'Serviços Financeiros', 'Serviços Financeiros', 'Alimentício', 'Construção', 'Construção', 'Serviços Financeiros', 'Varejo', 'Energia', 'Serviços Financeiros',
              'Serviços Financeiros', 'Energia', 'Varejo', 'Petróleo e Gás', 'Energia', 'Serviços Financeiros', 'Serviços Financeiros', 'Energia', 'Construção', 'Alimentício',
              'Construção', 'Serviços Financeiros', 'Serviços Financeiros', 'Serviços Financeiros', 'Energia', 'Serviços Financeiros', 'Serviços Financeiros', 'Varejo', 'Varejo', 'Construção', 'Energia']
}

empresaschi = {
    'empresa': ['Banco Santander Chile', 'LATAM Airlines Group S.A.', 'Cencosud S.A.', 'Enel Chile S.A.', 'SQM S.A.', 'Banco de Chile',
                'CAP S.A.', 'Embotelladora Andina S.A.', 'Empresa Nacional de Electricidad S.A.', 'Banco BICE', 'Colbún S.A.', 'Copec S.A.',
                'Entel Chile S.A.', 'Empresas Copec S.A.', 'SMU S.A.', 'Falabella S.A.', 'Banco Santander Chile', 'Banco de Crédito e Inversiones',
                'ILC Grupo Security S.A.', 'Sonda S.A.', 'Banco Estado', 'Parque Arauco S.A.', 'Itaú Corpbanca', 'Viña Concha y Toro S.A.',
                'Sociedad Matriz SAAM S.A.', 'Banco Santander Chile', 'Grupo Security S.A.', 'Enel Distribucion Chile S.A.', 'Inversiones La Construcción S.A.', 'BCI Seguros S.A.'],
    'codigo': ['SAN.SN', 'LTM', 'CENCOSUD', 'ENELCHILE', 'SQM', 'BCH', 'CAP', 'ANDINA-A', 'ENELAM', 'BICE', 'COLBUN', 'COPEC',
               'ENTEL', 'COPEC', 'SMU', 'FALABELLA', 'BSANTANDER', 'BCI', 'ILC', 'SONDA', 'ESTADO', 'PARAUCO', 'ITAUCORP', 'CONCHATORO',
               'SAAM', 'BSAN.SN', 'SECURITY', 'ENELCHILE', 'ILC', 'BCI'],
    'pais': ['Chile'] * 30,
    'nicho': ['Serviços Financeiros', 'Transporte Aéreo', 'Varejo', 'Energia', 'Mineração', 'Serviços Financeiros', 'Indústria', 'Indústria', 'Energia', 'Serviços Financeiros',
              'Energia', 'Energia', 'Telecomunicações', 'Indústria', 'Varejo', 'Varejo', 'Serviços Financeiros', 'Serviços Financeiros', 'Serviços Financeiros', 'Tecnologia',
              'Tecnologia', 'Serviços Financeiros', 'Imobiliário', 'Serviços Financeiros', 'Bebidas', 'Serviços Financeiros', 'Serviços Financeiros', 'Energia', 'Serviços Financeiros', 'Seguros']
}

empresasper = {
    'empresa': ['Credicorp Ltd.', 'Southern Copper Corporation', 'Volcan Compañía Minera S.A.A.', 'Banco de Crédito del Perú', 'Grana y Montero S.A.A.', 'Engie Energia Perú S.A.',
                'Ferreyros S.A.A.', 'Minera Buenaventura S.A.A.', 'Banco Continental', 'Intercorp Financial Services Inc.', 'Lima Airport Partners S.R.L.', 'Cementos Pacasmayo S.A.A.',
                'Graña y Montero S.A.A.', 'Inretail Peru Corporation S.A.', 'Inmobiliaria Panamericana S.A.A.', 'Alicorp S.A.A.', 'Hochschild Mining plc', 'Empresas Copec S.A.', 'Backus and Johnston',
                'Aceros Arequipa S.A.', 'Refinería La Pampilla S.A.A.', 'Pacífico Seguros', 'Alicorp S.A.A.', 'E.W. Scripps Company', 'Gloria S.A.', 'Cencosud Shopping Centers S.A.', 'Rímac Seguros y Reaseguros S.A.',
                'Ferreyros S.A.A.', 'Inmobiliaria Inversiones La Construcción S.A.A.'],
    'codigo': ['BAP', 'SCCO', 'VOLCABC1', 'BAP', 'GRAMONC1', 'ENGIEC1', 'FERREYC1', 'BUE', 'BAP', 'IFS', 'AAPL1', 'CPACASC1', 'GRAMONC1', 'INRETC1', 'PAPAC1', 'ALICORC1',
               'HOC.L', 'COPEC', 'BAP', 'BAP', 'RLP', 'BAP', 'ALICORC1', 'PRSGA', 'EWSCC1', 'PFA', 'CENCOSUD', 'RIMAC1', 'FERREYC1', 'ILCC1'],
    'pais': ['Peru'] * 30,
    'nicho': ['Serviços Financeiros', 'Mineração', 'Mineração', 'Serviços Financeiros', 'Construção', 'Energia', 'Construção', 'Mineração', 'Serviços Financeiros', 'Serviços Financeiros',
              'Transporte', 'Construção', 'Construção', 'Varejo', 'Imobiliário', 'Alimentício', 'Mineração', 'Energia', 'Bebidas', 'Manufatura',
              'Petróleo e Gás', 'Seguros', 'Alimentício', 'Mídia', 'Alimentício', 'Varejo', 'Seguros', 'Construção', 'Imobiliário']
}

empresas_tecnologicas = {
    'empresa': ['Apple Inc.', 'Microsoft Corporation', 'Amazon.com Inc.', 'Alphabet Inc.', 'Facebook, Inc.', 'Tesla, Inc.', 'NVIDIA Corporation',
                'Adobe Inc.', 'Intel Corporation', 'IBM (International Business Machines Corporation)', 'Netflix, Inc.', 'Salesforce.com, Inc.',
                'Tencent Holdings Limited', 'Oracle Corporation', 'Cisco Systems, Inc.', 'Qualcomm Incorporated', 'PayPal Holdings, Inc.', 'Sony Corporation',
                'Square, Inc.', 'Twitter, Inc.', 'Uber Technologies, Inc.', 'Zoom Video Communications, Inc.', 'Shopify Inc.', 'Palantir Technologies Inc.',
                'Alibaba Group Holding Limited', 'Snowflake Inc.', 'Pinterest, Inc.', 'DocuSign, Inc.', 'Twilio Inc.', 'ServiceNow, Inc.'],
    'codigo': ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'ADBE', 'INTC', 'IBM', 'NFLX', 'CRM', 'TCEHY', 'ORCL', 'CSCO', 'QCOM', 'PYPL', 'SNE',
               'SQ', 'TWTR', 'UBER', 'ZM', 'SHOP', 'PLTR', 'BABA', 'SNOW', 'PINS', 'DOCU', 'TWLO', 'NOW'],
    'pais': ['EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'China', 'EUA', 'EUA', 'EUA', 'EUA', 'Japão', 'EUA',
             'EUA', 'EUA', 'EUA', 'Canadá', 'EUA', 'China', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA'],
    'nicho': ['Tecnologia'] * 30
}

empresas_financeiras = {
    'empresa': ['JPMorgan Chase & Co.', 'Berkshire Hathaway Inc.', 'Bank of America Corporation', 'Wells Fargo & Company', 'Citigroup Inc.', 'Goldman Sachs Group, Inc.',
                'Morgan Stanley', 'American Express Company', 'Mastercard Incorporated', 'Visa Inc.', 'The Charles Schwab Corporation', 'BlackRock, Inc.',
                'S&P Global Inc.', 'Fidelity National Information Services, Inc.', 'Fiserv, Inc.', 'Capital One Financial Corporation', 'Nasdaq, Inc.',
                'The Bank of New York Mellon Corporation', 'T. Rowe Price Group, Inc.', 'State Street Corporation', 'BB&T Corporation', 'Northern Trust Corporation',
                'Ally Financial Inc.', 'E*TRADE Financial Corporation', 'Discover Financial Services', 'Intercontinental Exchange, Inc.', 'Ameriprise Financial, Inc.',
                'CME Group Inc.', 'Raymond James Financial, Inc.', 'The Travelers Companies, Inc.'],
    'codigo': ['JPM', 'BRK.B', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'MA', 'V', 'SCHW', 'BLK', 'SPGI', 'FIS', 'FISV', 'COF', 'NDAQ', 'BK', 'TROW', 'STT', 'BBT', 'NTRS',
               'ALLY', 'ETFC', 'DFS', 'ICE', 'AMP', 'CME', 'RJF', 'TRV'],
    'pais': ['EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA',
             'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA'],
    'nicho': ['Serviços Financeiros'] * 30
}

empresas_energia = {
    'empresa': ['Saudi Aramco', 'Exxon Mobil', 'Royal Dutch Shell', 'China National Petroleum Corporation', 'BP', 'TotalEnergies', 'Saudi Arabian Oil Company', 'Chevron Corporation', 'Gazprom', 'Rosneft',
                'Kuwait Petroleum Corporation', 'PetroChina', 'Eni', 'Abu Dhabi National Oil Company', 'Sinopec', 'Valero Energy', 'Phillips 66', 'Petrobras', 'Reliance Industries', 'PetroChina', 
                'Equinor', 'PT Pertamina (Persero)', 'ConocoPhillips', 'EOG Resources', 'Lukoil', 'Marathon Petroleum', 'Pemex', 'Saudi Basic Industries Corporation (SABIC)', 'Enbridge', 'BHP',
                'Exxon Mobil', 'E.ON', 'Petronas', 'Petronas Chemicals Group Berhad', 'NextEra Energy', 'Suncor Energy', 'Indian Oil Corporation', 'Occidental Petroleum', 'Duke Energy', 'Chesapeake Energy',
                'Southern Company', 'Schlumberger', 'Canadian Natural Resources', 'Chevron Corporation', 'Woodside Petroleum', 'ConocoPhillips', 'EOG Resources', 'Repsol', 'EOG Resources', 'Devon Energy'],
    'codigo': ['ARAMCO', 'XOM', 'RDS.A', 'PTR', 'BP', 'TTE', '2222.SE', 'CVX', 'OGZPY', 'ROSN.ME', 'KPC', 'PTR', 'ENI', 'ABD.NE', 'SNP', 'VLO', 'PSX', 'PBR', 'RELIANCE.NS', 'PTR', 
               'EQNR', 'PERT.JK', 'COP', 'EOG', 'LKOH.ME', 'MPC', 'PXX', '2010.SE', 'ENB', 'BHP', 'XOM', 'EONGY', 'PETRONM', '5183.KL', 'NEE', 'SU', 'IOCL.NS', 'OXY', 'DUK', 'CHK',
               'SO', 'SLB', 'CNQ', 'CVX', 'WPL.AX', 'COP', 'EOG', 'REP.MC', 'EOG', 'DVN'],
    'pais': ['Arábia Saudita', 'EUA', 'Reino Unido / Países Baixos', 'China', 'Reino Unido', 'França', 'Arábia Saudita', 'EUA', 'Rússia', 'Rússia', 'Kuwait', 'China', 'Itália', 'Emirados Árabes Unidos',
             'China', 'EUA', 'EUA', 'Brasil', 'Índia', 'China', 'Noruega', 'Indonésia', 'EUA', 'EUA', 'Rússia', 'EUA', 'México', 'Arábia Saudita', 'Canadá', 'Austrália', 'EUA', 'Alemanha',
             'Malásia', 'Malásia', 'EUA', 'Canadá', 'Índia', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'Canadá', 'EUA', 'Austrália', 'EUA', 'EUA', 'Espanha', 'EUA', 'EUA'],
    'nicho': ['Energia'] * 50
}

empresas_automotivas = {
    'empresa': ['Toyota', 'Volkswagen', 'Daimler', 'General Motors', 'BMW', 'Honda', 'Ford', 'Nissan', 'Tesla', 'Hyundai', 'Audi', 'Volvo', 'Fiat Chrysler', 'Renault', 'Peugeot', 'Subaru', 'Kia', 'Mazda', 'Jaguar Land Rover', 'Mercedes-Benz',
                'Mitsubishi', 'Porsche', 'Geely', 'BYD', 'Tata Motors', 'Suzuki', 'Ferrari', 'Bentley', 'Lamborghini', 'Rolls-Royce'],
    'codigo': ['TM', 'VWAGY', 'DDAIF', 'GM', 'BMWYY', 'HMC', 'F', 'NSANY', 'TSLA', 'HYMTF', 'AUDVF', 'VOLVY', 'FCAU', 'RNSDF', 'PUGOY', 'FUJHY', 'HYMTF', 'MZDAY', 'TTM', 'DDAIF',
               'MSBHY', 'POAHY', 'GELYY', 'BYDDY', 'TTM', 'SZKMY', 'RACE', 'BNTGF', 'VLKAF', 'RYCEY'],
    'pais': ['Japão', 'Alemanha', 'Alemanha', 'EUA', 'Alemanha', 'Japão', 'EUA', 'Japão', 'EUA', 'Coreia do Sul', 'Alemanha', 'Suécia', 'Itália', 'França', 'França', 'Japão', 'Coreia do Sul', 'Japão', 'Reino Unido', 'Alemanha',
             'Japão', 'Alemanha', 'China', 'China', 'Índia', 'Japão', 'Itália', 'Reino Unido', 'Itália', 'Reino Unido'],
    'nicho': ['Automotiva'] * 30
}
empresas_varejo = {
    'empresa': ['Walmart', 'Amazon', 'Alibaba', 'Costco', 'Home Depot', 'Tesco', 'Lowe\'s', 'Aldi', 'Inditex', 'Carrefour', 'JD.com', 'Target', 'IKEA', 'CVS Health', 'LVMH', 'Woolworths', 'Kroger', 'Lidl', 'Seven & i Holdings', 'Walgreens Boots Alliance',
                'Best Buy', 'Shopify', 'Coles Group', 'Schwarz Group', 'Sainsbury\'s', 'Metro AG', 'Yum China Holdings', 'Ross Stores', 'X5 Retail Group', 'Macy\'s', 'Ahold Delhaize', 'Next plc', 'Zalando', 'Rite Aid', 'Fast Retailing', 'H&M', 'Gap', 'L Brands',
                'Canadian Tire', 'O\'Reilly Auto Parts', 'Kingfisher', 'Ulta Beauty', 'Migros', 'Jeronimo Martins', 'Tractor Supply Company', 'J. Sainsbury', 'Marks & Spencer', 'Dollar General', 'Casino Guichard-Perrachon'],
    'codigo': ['WMT', 'AMZN', 'BABA', 'COST', 'HD', 'TSCO', 'LOW', '', 'ITX', 'CA', 'JD', 'TGT', '', 'CVS', 'LVMUY', 'WOW', 'KR', '', '', '', 'WBA', 'BBY', 'SHOP', '', '', '', '', 'YUMC', 'ROST', '', 'M', 'ADRNY', 'NXT',
               'ZAL', 'RAD', 'FRCOY', 'HNNMY', 'GPS', 'LB', 'CDNAF', 'ORLY', '', 'ULTA', '', '', 'JMT', 'TSCO', 'SBRY', 'MAKSY', 'DG', 'CGUSY'],
    'pais': ['EUA', 'EUA', 'China', 'EUA', 'EUA', 'Reino Unido', 'EUA', 'Alemanha', 'Espanha', 'França', 'China', 'EUA', 'Suécia', 'EUA', 'França', 'Austrália', 'EUA', 'Alemanha', 'Japão', 'EUA', 'EUA', 'Canadá', 'Austrália', 'Alemanha',
             'Reino Unido', 'Alemanha', 'China', 'EUA', 'Rússia', 'EUA', 'Holanda', 'Reino Unido', 'Alemanha', 'EUA', 'Suécia', 'EUA', 'EUA', 'Canadá', 'EUA', 'Reino Unido', 'EUA', 'Suíça', 'Portugal', 'EUA', 'Reino Unido', 'Reino Unido',
             'EUA', 'França'],
    'nicho': ['Varejo'] * 30
}

empresas_saude = {
    'empresa': ['Johnson & Johnson', 'Roche Holding', 'Pfizer', 'Novartis', 'Merck & Co.', 'Abbott Laboratories', 'Sanofi', 'GlaxoSmithKline', 'Medtronic', 'Bristol-Myers Squibb',
                'Eli Lilly and Company', 'Amgen', 'AstraZeneca', 'Novo Nordisk', 'Takeda Pharmaceutical', 'Gilead Sciences', 'Bayer', 'Becton Dickinson', 'Teva Pharmaceutical Industries', 'Stryker',
                'AbbVie', 'Biogen', 'Regeneron Pharmaceuticals', 'Vertex Pharmaceuticals', 'Alexion Pharmaceuticals', 'Shire', 'Zoetis', 'Fresenius', 'Cigna', 'Cardinal Health'],
    'codigo': ['JNJ', 'ROG', 'PFE', 'NOVN', 'MRK', 'ABT', 'SNY', 'GSK', 'MDT', 'BMY', 'LLY', 'AMGN', 'AZN', 'NVO', '4502.T', 'GILD', 'BAYN', 'BDX', 'TEVA', 'SYK',
               'ABBV', 'BIIB', 'REGN', 'VRTX', 'ALXN', 'SHPG', 'ZTS', 'FRE', 'CI', 'CAH'],
    'pais': ['EUA', 'Suíça', 'EUA', 'Suíça', 'EUA', 'EUA', 'França', 'Reino Unido', 'EUA', 'EUA', 'EUA', 'EUA', 'Reino Unido', 'Dinamarca', 'Japão', 'EUA', 'Alemanha', 'EUA', 'Israel', 'EUA',
             'EUA', 'EUA', 'EUA', 'EUA', 'EUA', 'Irlanda', 'EUA', 'Alemanha', 'EUA', 'EUA', 'EUA'],
    'nicho': ['Saúde'] * 30
}

empresas_construcao_civil = {
    'empresa': ['China State Construction Engineering', 'China Railway Group', 'China Railway Construction', 'Vinci', 'ACS', 'Bouygues', 'Larsen & Toubro', 'Actividades de Construcción y Servicios', 'China Communications Construction', 'China Evergrande Group',
                'Shimizu', 'Skanska', 'Bechtel', 'China Metallurgical Group', 'Power Construction Corporation of China', 'Obayashi Corporation', 'China Energy Engineering Corporation', 'Shanghai Construction Group', 'China National Building Material Group', 'China Resources Cement Holdings',
                'VINCI Construction', 'China Gezhouba Group', 'CRH', 'China Railway Engineering Corporation', 'China National Machinery Industry Corporation', 'Sinohydro Group', 'Grupo ACS', 'China Railway Signal & Communication', 'China Communications Services Corporation', 'Beijing Urban Construction Group',
                'China National Erzhong Group', 'China National Nuclear Corporation', 'Balfour Beatty', 'Daikin Industries', 'United Technologies Corporation', 'Japan Airlines', 'China National Aviation Holding', 'China Southern Airlines', 'Air China', 'Delta Air Lines',
                'Sinopec', 'PetroChina', 'ExxonMobil', 'Royal Dutch Shell', 'Chevron', 'Total', 'BP', 'Petrobras', 'Schlumberger'],
    'codigo': ['601668.SS', '0390.HK', '1186.HK', 'DG.PA', 'ACS.MC', 'EN.PA', 'LT.NS', 'ACS.MC', '1800.HK', '3333.HK',
               '1803.T', 'SKA-B.ST', 'Privada', '1618.HK', '601669.SS', '1802.T', '601800.SS', '600170.SS', '601668.SS', '1899.HK', '1313.HK',
               'DG.PA', '600068.SS', 'CRG.IR', '3898.HK', 'SINOVIS.BO', '601618.SS', 'ACS.MC', '600548.SS', '0554.HK', 'Privada',
               '601268.SS', '601985.SS', 'BALF.L', '6367.T', 'UTX', '9201.T', '601111.SS', '1055.HK', '601111.SS', '601111.SS',
               '600028.SS', '601857.SS', 'XOM', 'RDS-A', 'CVX', 'FP.PA', 'BP', 'PBR', 'SLB'],
    'pais': ['China', 'China', 'China', 'França', 'Espanha', 'França', 'Índia', 'Espanha', 'China', 'China',
             'Japão', 'Suécia', 'Estados Unidos', 'China', 'China', 'Japão', 'China', 'China', 'China', 'China',
             'França', 'China', 'Irlanda', 'China', 'China', 'China', 'Espanha', 'China', 'China', 'China',
             'China', 'China', 'Reino Unido', 'Japão', 'Estados Unidos', 'Japão', 'China', 'China', 'China',
             'China', 'EUA', 'Holanda', 'EUA', 'EUA', 'França', 'Reino Unido', 'Brasil', 'EUA'],
    'nicho': ['Construção Civil'] * 50
}

empresas_mineracao = {
    'empresa': [
        "BHP Group", "Rio Tinto", "Vale", "Glencore", "Anglo American", "Freeport-McMoRan", "Newmont Corporation", "Barrick Gold", "Teck Resources", "South32",
        "Alcoa Corporation", "Gold Fields", "Newcrest Mining", "Fortescue Metals Group", "Southern Copper Corporation", "Aluminum Corporation of China Limited (Chalco)", "Codelco", "Nornickel", "Mosaic", "Lynas Rare Earths",
        "Vale Indonesia", "First Quantum Minerals", "Wheaton Precious Metals", "Hudbay Minerals", "Turquoise Hill Resources", "OZ Minerals", "Lundin Mining Corporation", "Evolution Mining", "Pan American Silver", "Northern Star Resources",
        "Kinross Gold Corporation", "Hecla Mining Company", "Yamana Gold", "SSR Mining", "Kirkland Lake Gold", "Alamos Gold", "Iamgold Corporation", "Agnico Eagle Mines Limited", "New Gold Inc.", "Endeavour Mining Corporation", "Harmony Gold Mining Company Limited",
        "Centamin plc", "Hochschild Mining plc", "MAG Silver Corporation", "Pretium Resources Inc.", "Osisko Gold Royalties Ltd", "Shandong Gold Mining Co., Ltd.", "Silvercorp Metals Inc.", "Royal Gold, Inc.", "Polymetal International plc", "Sandstorm Gold Ltd.",
        "Northern Dynasty Minerals Ltd.", "Fortuna Silver Mines Inc.", "Lundin Gold Inc."
    ],
    'codigo': [
        "BHP", "RIO", "VALE", "GLEN.L", "AAL.L", "FCX", "NEM", "GOLD", "TECK", "S32",
        "AA", "GFI", "NCM.AX", "FMG.AX", "SCCO", "2600.HK", "CODEL.SN", "GMKN.ME", "MOS", "LYC.AX",
        "INCO.JK", "FM.TO", "WPM", "HBM", "TRQ", "OZL.AX", "LUN.TO", "EVN.AX", "PAAS", "NST.AX",
        "KGC", "HL", "AUY", "SSRM", "KL", "AGI", "IAG", "AEM", "NGD", "EDV.TO", "HMY",
        "CEY.L", "HOC.L", "MAG", "PVG", "OR.TO", "600547.SS", "SVM", "RGLD", "POLY.L", "SAND",
        "NAK", "FSM", "LUG.TO"
    ],
    'pais': [
        'Austrália', 'Austrália', 'Brasil', 'Suíça', 'Reino Unido', 'Estados Unidos', 'Estados Unidos', 'Canadá', 'Canadá', 'Austrália',
        'Estados Unidos', 'África do Sul', 'Austrália', 'Austrália', 'Peru', 'China', 'Chile', 'Rússia', 'Estados Unidos', 'Austrália',
        'Indonésia', 'Canadá', 'Canadá', 'Canadá', 'Estados Unidos', 'Austrália', 'Canadá', 'Austrália', 'Estados Unidos', 'Austrália',
        'Canadá', 'Estados Unidos', 'Canadá', 'Estados Unidos', 'Canadá', 'Canadá', 'Canadá', 'Canadá', 'Canadá', 'Canadá', 'Reino Unido',
        'Reino Unido', 'Canadá', 'Canadá', 'Canadá', 'China', 'Canadá', 'Reino Unido', 'Rússia', 'Canadá', 'Canadá',
        'Estados Unidos', 'Canadá', 'Canadá'
    ],
    'nicho': ['Mineração'] * 50
}

indices_bolsas = {
    'empresa': [
        "Ibovespa", "S&P 500", "NASDAQ Composite", "FTSE 100", "DAX", "CAC 40", "Nikkei 225", "Hang Seng", "Shanghai Composite", "BSE Sensex",
        "KOSPI", "S&P/ASX 200", "TSX Composite", "IBEX 35", "FTSE MIB", "RTS Index", "MOEX Russia", "Bovespa", "IPC Mexico", "IPC Colombia",
        "MERVAL", "S&P/BMV IPC", "S&P/CLX IPSA", "BVC Bolivia", "BVN Peru", "IMC Chile", "BGS Paraguay", "IGBVL", "MSE Top 20 Index", "JSE All Share"
    ],
    'codigo': [
        "^BVSP", "^GSPC", "^IXIC", "^FTSE", "^GDAXI", "^FCHI", "^N225", "^HSI", "000001.SS", "^BSESN",
        "^KS11", "^AXJO", "^GSPTSE", "^IBEX", "FTSEMIB.MI", "^RTSI", "^IMOEX.ME", "^BVSP", "^MXX", "^COLCAP",
        "^MERV", "^MXX", "^IPSA", "^BVP", "^SPBLPGPT", "^IGPA", "^BVLG", "^ITC", "^JALSH"
    ],
    'pais': [
        "Brasil", "Estados Unidos", "Estados Unidos", "Reino Unido", "Alemanha", "França", "Japão", "Hong Kong", "China", "Índia",
        "Coreia do Sul", "Austrália", "Canadá", "Espanha", "Itália", "Rússia", "Rússia", "Brasil", "México", "Colômbia",
        "Argentina", "México", "Chile", "Bolívia", "Peru", "Chile", "Paraguai", "Peru", "Mongólia", "África do Sul"
    ],
    'nicho': ['Índices das Bolsas'] * 30
}

'''

