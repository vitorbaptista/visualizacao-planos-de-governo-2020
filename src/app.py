import os
import gzip
import datetime

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATA_RAW_PATH = 'data/raw/'
PLANOS_PATH = os.path.join(DATA_RAW_PATH, 'planos-de-governo.csv')

"""
# Eleições 2020 - Planos de governo

Esta página permite visualizar em uma única página todos os planos de
governo dos candidatos de um município.

## Como usar?

Depois de selecionar um município na caixa de Município abaixo, os planos de
governo dos candidatos serão carregados nesta página. A partir daí, você pode
usar a busca do seu navegador, usando CTRL+F, para procurar por
palavras-chave que te interessem.

## Créditos

Criado por [Vitor Baptista](https://twitter.com/vitorbaptista), usando os
dados do sistema [Tribunal Superior Eleitoral
(TSE)](https://divulgacandcontas.tse.jus.br/divulga/) extraídos por [Augusto
Hermann](https://ecodigital.social/@herrmann) e [Ana Paula
Gomes](https://twitter.com/anapaulagomess) em
[https://github.com/augusto-herrmann/eleicoes-2020-planos-de-governo](https://github.com/augusto-herrmann/eleicoes-2020-planos-de-governo).
"""

st.title('Eleições 2020 - Planos de governo')

@st.cache
def load_data():
    df = pd.read_csv(PLANOS_PATH, parse_dates=['data_nascimento'])
    df['data_nascimento'] = df['data_nascimento'].dt.date
    df['uf_municipio'] = df['sigla_estado'] + ' - ' + df['municipio']

    for col in ['nome_urna', 'genero', 'grau_instrucao', 'ocupacao', 'cor_raca']:
        df[col] = df[col].str.title()
    df['estado_civil'] = df['estado_civil'].str.capitalize()
    df['arquivo'] = df['arquivo'] + '.gz'

    df['candidato_reeleicao'].replace({
        'N': 'Não',
        'S': 'Sim',
    }, inplace=True)

    df['nome_partido'] = df['nome_urna'] + ' (' + df['sigla_partido'] + ')'
    # Aproximação da idade (não considera anos bissextos)
    now = datetime.datetime.now().date()
    df['idade'] = ((now - df['data_nascimento']).dt.days / 365).astype(int)

    return df

planos_df = load_data()

"""
# Candidatos
"""


# Setup select de Municípios, buscando código do município na URL se existir
municipios = {
    row['codigo_cidade_tse']: row['uf_municipio']
    for _, row in planos_df[['codigo_cidade_tse', 'uf_municipio']].drop_duplicates().sort_values(by='uf_municipio').iterrows()
}
codigos_municipios = list(municipios.keys())

query_params = st.experimental_get_query_params()
try:
    selected_municipio = int(query_params.get('municipio', ['20516'])[0])  # João Pessoa
    default_municipio_index = codigos_municipios.index(selected_municipio)
except ValueError:
    default_municipio_index = 0
codigo_cidade = st.selectbox(
    'Município',
    codigos_municipios,
    format_func=lambda municipio: municipios[municipio],
    index=default_municipio_index
)
st.experimental_set_query_params(municipio=codigo_cidade)


# Carrega texto das propostas
@st.cache
def load_propostas(arquivo):
    path = os.path.join(DATA_RAW_PATH, arquivo)
    try:
        txt = gzip.open(path, mode='rt').read().strip()
    except FileNotFoundError:
        txt = None
    return txt


@st.cache
def load_uf_df(df, codigo_cidade):
    uf_df = df[df['codigo_cidade_tse'] == codigo_cidade].copy()
    uf_df['propostas_txt'] = df['arquivo'].apply(load_propostas)
    return uf_df.sort_values(by='nome_urna')


planos_municipio_df = load_uf_df(planos_df, codigo_cidade)

# Mostra tabela com candidatos
columns_renames = {
    'nome_urna': 'Nome',
    'sigla_partido': 'Partido',
    'genero': 'Gênero',
    'cor_raca': 'Raça',
    'ocupacao': 'Ocupação',
    'idade': 'Idade',
    'candidato_reeleicao': 'Reeleição?',
}
st.table(
    planos_municipio_df[columns_renames.keys()] \
        .rename(columns=columns_renames) \
        .reset_index().drop(columns=['index'])
)

"""
# Planos de governo
"""

css = """
<style>
.propostas-titulo {
    position: sticky;
    position: -webkit-sticky;
    top: 0px;
    background-color: white;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)
for _, row in planos_municipio_df.iterrows():
    pdf_link = ''
    if isinstance(row['url'], str):
        pdf_link = f'<a href="{row["url"]}" target="_blank">Ver PDF</a>'

    html = f"""
      <arcticle>
        <h2 class="propostas-titulo">
          {row['nome_partido']} {pdf_link}
        </h2>
        {row['propostas_txt'] or 'Vazio'}
      </arcticle>
    """
    st.markdown(html, unsafe_allow_html=True)
