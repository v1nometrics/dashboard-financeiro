import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import json
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import boto3
import datetime
from io import BytesIO
from PIL import Image

# Carregar flat logo via URL direta
logo_flat = 'https://www.innovatismc.com.br/wp-content/uploads/2023/12/logo-innovatis-flatico-150x150.png'
st.set_page_config(layout="wide", page_title='DASHBOARD v1.0', page_icon=logo_flat)

# Importa a fonte Poppins do Google Fonts
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        [class^=st-emotion] {
            font-family: 'Poppins', sans-serif !important;
        }
        body * {
            font-family: 'Poppins', sans-serif !important;
        }
    </style>
""", unsafe_allow_html=True)

# Título do aplicativo
st.title('Dashboard Financeiro (v1.0)')

# Importar arquivo de configuração
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Criar o objeto de autenticação
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

# Verificação do status da autenticação
if st.session_state["authentication_status"]:
    authenticator.logout("Logout", "sidebar")
    st.write(f"Bem-vindo, {st.session_state['name']}!")
elif st.session_state["authentication_status"] is False:
    st.error('Usuário/Senha inválido')
if st.session_state["authentication_status"] is None:
    st.markdown("""
        <style>
        div[data-testid="stAppViewContainer"] {
            max-width: 600px;
            margin: auto;
        }
        </style>
    """, unsafe_allow_html=True)
    st.warning('Por Favor, utilize seu usuário e senha!')

# O resto do código só executa se autenticado
if st.session_state["authentication_status"]:
    
    # Configurar acesso ao S3
    s3 = boto3.client('s3')
    s3 = boto3.resource(
        service_name='s3',
        region_name='us-east-2',
        aws_access_key_id='AKIA47GB733YQT2N7HNC',
        aws_secret_access_key='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'
    )

    @st.cache_data
    def carregar_planilha():
        # Baixar o arquivo JSON diretamente do S3
        obj = s3.Bucket('jsoninnovatis').Object('chave2.json').get()
        # Ler o conteúdo do objeto, decodificar para string e converter para dict
        creds_json = json.loads(obj['Body'].read().decode('utf-8'))
        # Definir o escopo de acesso para Google Sheets e Google Drive
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Criar as credenciais a partir do JSON baixado
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        # Acessar a planilha do Google
        planilha = client.open("AJUSTADA - Valores a receber Innovatis").worksheet("VALORES A RECEBER")
        st.write("Conectado à planilha com sucesso!")
        # Obter todos os dados da planilha
        dados = planilha.get_all_records()
        # Converter os dados para um DataFrame
        df = pd.DataFrame(dados)
        return df

    # Carregar os dados brutos e armazenar em uma variável global
    df_raw = carregar_planilha()

    @st.cache_data
    def preprocess_data(df):
        # Remover espaços e ajustar nomes de colunas
        df.columns = df.columns.str.strip().str.replace(' ', '_')
        data = df[['FUNDAÇÃO', 'CLIENTE', 'TIPO', 'PREVISÃO_DE_RECEBIMENTO', 'ANO',
                   'SALDO_A_RECEBER', 'CUSTOS_INCORRIDOS', 'OUTROS_E_CORRELATOS']].copy()
        data = data.rename(columns={'OUTROS_E_CORRELATOS': 'CUSTOS_CORRELATOS'})
        
        # Transformar e unificar colunas para criação da DATA
        data['PREVISÃO_DE_RECEBIMENTO'] = data['PREVISÃO_DE_RECEBIMENTO'].str.strip().replace({
            'Janeiro': '01', 'JANEIRO': '01', 'Fevereiro': '02', 'FEVEREIRO': '02',
            'Março': '03', 'MARÇO': '03', 'Abril': '04', 'ABRIL': '04',
            'Maio': '05', 'MAIO': '05', 'Junho': '06', 'JUNHO': '06',
            'Julho': '07', 'JULHO': '07', 'Agosto': '08', 'AGOSTO': '08',
            'Setembro': '09', 'SETEMBRO': '09', 'Outubro': '10', 'OUTUBRO': '10',
            'Novembro': '11', 'NOVEMBRO': '11', 'Dezembro': '12', 'DEZEMBRO': '12',
            'A DEFINIR': 'A definir', 'A Definir': 'A definir'
        })
        data['ANO'] = data['ANO'].astype(str).str.replace('.0', '')
        data['DATA'] = data['PREVISÃO_DE_RECEBIMENTO'] + '/' + data['ANO']
        data = data.drop(['PREVISÃO_DE_RECEBIMENTO', 'ANO'], axis=1)
        data['DATA'] = pd.to_datetime(data['DATA'], format='%m/%Y', errors='coerce')\
                        .dt.strftime('%m/%Y').fillna('A definir')
        data['CLIENTE'] = data['CLIENTE'].replace({'': 'Não identificado'})
        data = data[data['SALDO_A_RECEBER'] != '']
        data = data[data['TIPO'] != '']
        # Excluir datas específicas
        datas_excluir = ['01/2024', '02/2024', '03/2024', '04/2024', '05/2024', '06/2024',
                         '07/2024', '08/2024', '09/2024', '10/2024', '11/2024', '12/2024',
                         '01/2023', '02/2023', '03/2023', '04/2023', '05/2023', '06/2023',
                         '07/2023', '08/2023', '09/2023', '10/2023', '11/2023', '12/2023',
                         '01/2025']
        data = data[~data['DATA'].isin(datas_excluir)]
        data['TIPO'] = data['TIPO'].replace({'PROJETO/Empresa Privada': 'PROJETO'})
        
        # Remover o mês anterior
        today = datetime.date.today()
        first_day_this_month = datetime.date(today.year, today.month, 1)
        last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
        prev_month_str = last_day_prev_month.strftime('%m/%Y')
        data = data[data['DATA'] != prev_month_str]
        
        # Converter colunas de custo para numérico (vetorizado)
        for col in ['CUSTOS_INCORRIDOS', 'CUSTOS_CORRELATOS']:
            data[col] = (data[col].str.strip()
                         .str.replace('R\$', '', regex=True)
                         .str.replace('.', '')
                         .str.replace(',', '.'))
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data

    # Aplicar o pré-processamento e obter os dados processados
    data = preprocess_data(df_raw)

    @st.cache_data
    def load_data(nrows):
        return data.head(nrows)

    data_load_state = st.text('Carregando dados...')
    data = load_data(10000)
    data_load_state.text('Carregamento de dados concluído!')

    @st.cache_data
    def load_logo():
        logo_obj = s3.Bucket('jsoninnovatis').Object('Logo.png').get()
        logo_data = logo_obj['Body'].read()
        return Image.open(BytesIO(logo_data))

    logo_image = load_logo()
    st.sidebar.image(logo_image, use_container_width=True)
    
    st.markdown("""
        <style>
            [data-testid="stSidebar"] * {
                font-size: 101% !important;
            }
            .st-fx { background-color: rgb(49, 170, 77); }
            .st-cx { border-bottom-color: rgb(49, 170, 77); }
            .st-cw { border-top-color: rgb(49, 170, 77); }
            .st-cv { border-right-color: rgb(49, 170, 77); }
            .st-cu { border-left-color: rgb(49, 170, 77); }
            .st-ei { background-color: #28a74500 !important; }
            .st-e2 { background: linear-gradient(to right, rgba(151, 166, 195, 0.25) 0%, rgba(151, 166, 195, 0.25) 0%, rgb(49 170 77 / 0%) 0%, rgb(49 170 77 / 0%) 100%, rgba(151, 166, 195, 0.25) 100%, rgba(151, 166, 195, 0.25) 100%); }
            .st-e3 { background: linear-gradient(to right, rgba(151, 166, 195, 0.25) 0%, rgba(151, 166, 195, 0.25) 0%, rgb(49, 170, 77) 0%, rgb(49, 170, 77) 100%, rgba(151, 166, 195, 0.25) 100%, rgba(151, 166, 195, 0.25) 100%); }
            .st-emotion-cache-1dj3ksd { background-color: #28a745 !important; }
            .st-emotion-cache-15fru4 { padding: 0.2em 0.4em; overflow-wrap: break-word; margin: 0px; border-radius: 0.25rem; background: rgb(248, 249, 251); color: rgb(9, 171, 59); font-family: "Source Code Pro", monospace; font-size: 0.75em; }
            .st-emotion-cache-1373cj4 { font-family: "Source Code Pro", monospace; font-size: 14px; color: rgb(49, 170, 77); top: -1.6em; position: absolute; white-space: nowrap; background-color: transparent; line-height: 1.6; font-weight: 400; pointer-events: none; }
            .st-fi { background-color: rgb(49, 170, 77); }
            .st-hy { background-color: rgb(49, 170, 77); }
            .st-f1 { background-color: rgb(49, 170, 77); }
        </style>
    """, unsafe_allow_html=True)
    
    # Filtros interativos
    st.sidebar.header('Filtros')
    meses = st.sidebar.multiselect('Meses:', data['DATA'].unique())
    tipos = st.sidebar.multiselect('Tipos de Serviço:', data['TIPO'].unique())
    fundacoes = st.sidebar.multiselect('Fundações:', data['FUNDAÇÃO'].unique())
    clientes = st.sidebar.multiselect('Clientes:', data['CLIENTE'].unique())
    
    saldo_receber_temp = (data['SALDO_A_RECEBER']
                          .str.strip()
                          .str.replace('R$', '')
                          .str.replace('.', '')
                          .str.replace(',', '.'))
    saldo_receber_temp = pd.to_numeric(saldo_receber_temp, errors='coerce')
    
    min_saldo, max_saldo = st.sidebar.slider(
        'Selecione o intervalo de valores:',
        min_value=float(saldo_receber_temp.min()),
        max_value=float(saldo_receber_temp.max()),
        value=(float(saldo_receber_temp.min()), float(saldo_receber_temp.max())),
        step=1000.0
    )
    
    filtered_data = data.copy()
    if meses:
        filtered_data = filtered_data[filtered_data['DATA'].isin(meses)]
    if tipos:
        filtered_data = filtered_data[filtered_data['TIPO'].isin(tipos)]
    if fundacoes:
        filtered_data = filtered_data[filtered_data['FUNDAÇÃO'].isin(fundacoes)]
    if clientes:
        filtered_data = filtered_data[filtered_data['CLIENTE'].isin(clientes)]
    
    filtered_data['SALDO_A_RECEBER'] = saldo_receber_temp
    filtered_data = filtered_data[(filtered_data['SALDO_A_RECEBER'] >= min_saldo) &
                                  (filtered_data['SALDO_A_RECEBER'] <= max_saldo)]
    
    st.sidebar.subheader('Resumo dos Filtros')
    st.sidebar.write('Número de linhas:', filtered_data.shape[0])
    total_a_receber_filtrado = filtered_data['SALDO_A_RECEBER'].sum()
    total_a_receber_filtrado_real = f'R${total_a_receber_filtrado:,.2f}'
    st.sidebar.write('Valor Total a Receber:', total_a_receber_filtrado_real)
    
    st.subheader('Valor Total a Receber pela Empresa:')
    st.write(f'<p style="font-size:40px">{total_a_receber_filtrado_real}</p>', unsafe_allow_html=True)
    
    if st.checkbox('Mostrar planilha filtrada'):
        st.markdown("<h3 style='font-size:140%;'>Planilha de Contas a Receber - Higienizada em tempo real</h3>", unsafe_allow_html=True)
        st.write(filtered_data)
        st.markdown(f"<p style='font-size:140%;'>Tamanho da amostra: {filtered_data.shape[0]}</p>", unsafe_allow_html=True)
    
    # Criando colunas para os gráficos
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    # Definir paleta de cores
    colors_palette = ['#a1c9f4', '#a1f4c9', '#a1c9f4', '#a1f4c9', '#a1c9f4', '#a1f4c9', '#f4d1a1', '#f4a1d8']
    
    # Gráfico de barras horizontais - Distribuição por Cliente
    with row2_col1:
        st.subheader('Distribuição por Cliente')
        col_date, col_tipo, col_fundacao = st.columns(3)
        
        with col_date:
            datas_disponiveis = sorted(data['DATA'].unique())
            datas_selecionadas = st.multiselect("Data:", datas_disponiveis, default=[], key="data_cliente")
        with col_tipo:
            tipos_disponiveis = sorted(data['TIPO'].unique())
            tipos_selecionados = st.multiselect("Tipo de Serviço:", tipos_disponiveis, default=[], key="tipo_cliente")
        with col_fundacao:
            fundacoes_disponiveis = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas = st.multiselect("Fundação:", fundacoes_disponiveis, default=[], key="fundacao_cliente")
        
        dados_local = data.copy()
        if datas_selecionadas:
            dados_local = dados_local[dados_local['DATA'].isin(datas_selecionadas)]
        if tipos_selecionados:
            dados_local = dados_local[dados_local['TIPO'].isin(tipos_selecionados)]
        if fundacoes_selecionadas:
            dados_local = dados_local[dados_local['FUNDAÇÃO'].isin(fundacoes_selecionadas)]
        
        dados_local['SALDO_A_RECEBER'] = saldo_receber_temp
        
        total_por_cliente = dados_local.groupby('CLIENTE')['SALDO_A_RECEBER'].sum().reset_index()
        total_por_cliente = total_por_cliente.sort_values(by='SALDO_A_RECEBER', ascending=False)
        total_por_cliente['CLIENTE_AGRUPADO'] = total_por_cliente['CLIENTE']
        total_por_cliente.loc[
            total_por_cliente['SALDO_A_RECEBER'] / total_por_cliente['SALDO_A_RECEBER'].sum() < 0.03,
            'CLIENTE_AGRUPADO'
        ] = 'Outros'
        
        agrupado = total_por_cliente.groupby('CLIENTE_AGRUPADO')['SALDO_A_RECEBER'].sum().reset_index()
        agrupado = agrupado.sort_values(by='SALDO_A_RECEBER', ascending=True)
        agrupado['SALDO_A_RECEBER'] /= 1_000_000
        
        cores = colors_palette[:len(agrupado)]
        fig_bar, ax_bar = plt.subplots(figsize=(3, 2))
        ax_bar.barh(agrupado['CLIENTE_AGRUPADO'], agrupado['SALDO_A_RECEBER'], color=cores)
        ax_bar.set_xlabel('Saldo a Receber (em milhões)', fontsize=5)
        ax_bar.set_ylabel('Cliente', fontsize=5)
        ax_bar.ticklabel_format(style='plain', axis='x', useOffset=False)
        ax_bar.tick_params(axis='x', labelsize=4)
        ax_bar.tick_params(axis='y', labelsize=4)
        for i, v in enumerate(agrupado['SALDO_A_RECEBER']):
            ax_bar.text(v + (v * 0.01), i, f'R${v:,.2f}M', va='center', fontsize=4, color='black')
        st.pyplot(fig_bar, use_container_width=False)
    
    # Gráfico de Pizza: Distribuição dos Custos Incorridos e Correlatos
    with row2_col2:
        st.subheader('Distribuição dos Custos')
        col1, col2, col3 = st.columns(3)
        with col1:
            datas_disponiveis_custos = sorted(data['DATA'].unique())
            datas_selecionadas_custos = st.multiselect("Data:", datas_disponiveis_custos, default=[], key="data_custos")
        with col2:
            fundacoes_disponiveis_custos = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas_custos = st.multiselect("Fundação:", fundacoes_disponiveis_custos, default=[], key="fundacao_custos")
        with col3:
            clientes_disponiveis_custos = sorted(data['CLIENTE'].unique())
            clientes_selecionados_custos = st.multiselect("Cliente:", clientes_disponiveis_custos, default=[], key="cliente_custos")
        
        dados_local_custos = data.copy()
        if datas_selecionadas_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['DATA'].isin(datas_selecionadas_custos)]
        if fundacoes_selecionadas_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['FUNDAÇÃO'].isin(fundacoes_selecionadas_custos)]
        if clientes_selecionados_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['CLIENTE'].isin(clientes_selecionados_custos)]
        
        total_custos_incurridos = dados_local_custos['CUSTOS_INCORRIDOS'].sum()
        total_custos_correlatos = dados_local_custos['CUSTOS_CORRELATOS'].sum()
        custos_labels = ['Custos Incorridos', 'Custos Correlatos']
        custos_values = [total_custos_incurridos, total_custos_correlatos]
        color_map = {
            'Custos Incorridos': '#a1c9f4',
            'Custos Correlatos': '#a1f4c9'
        }
        custos_colors = [color_map[label] for label in custos_labels]
        
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = pct * total / 100.0
                return f'{pct:.1f}%\nR${val:,.2f}'
            return my_autopct
        
        fig_pizza, ax_pizza = plt.subplots(figsize=(2, 2))
        wedges, texts, autotexts = ax_pizza.pie(
            custos_values,
            labels=custos_labels,
            autopct=make_autopct(custos_values),
            startangle=60,
            colors=custos_colors,
            textprops={'fontsize': 5}
        )
        plt.legend(custos_labels, fontsize=5, loc='center left', bbox_to_anchor=(1, 0.5))
        ax_pizza.axis('equal')
        st.pyplot(fig_pizza, use_container_width=False)
    
    # Gráfico de barras - Distribuição de Valor a Receber por Fundação
    with row1_col1:
        st.subheader('Valor a Receber por Fundação')
        col_date, col_tipo = st.columns(2)
        with col_date:
            datas_disponiveis_fundacao = sorted(data['DATA'].unique())
            datas_selecionadas_fundacao = st.multiselect("Data:", datas_disponiveis_fundacao, default=[], key="data_fundacao")
        with col_tipo:
            tipos_disponiveis = sorted(data['TIPO'].unique())
            tipos_selecionados = st.multiselect("Tipo de Serviço:", tipos_disponiveis, default=[], key="tipo_fundacao")
        
        dados_local_fundacao = data.copy()
        if datas_selecionadas_fundacao:
            dados_local_fundacao = dados_local_fundacao[dados_local_fundacao['DATA'].isin(datas_selecionadas_fundacao)]
        if tipos_selecionados:
            dados_local_fundacao = dados_local_fundacao[dados_local_fundacao['TIPO'].isin(tipos_selecionados)]
        
        dados_local_fundacao['SALDO_A_RECEBER'] = saldo_receber_temp
        total_a_receber_por_fundacao = dados_local_fundacao.groupby('FUNDAÇÃO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_fundacao['SALDO_A_RECEBER'] = pd.to_numeric(total_a_receber_por_fundacao['SALDO_A_RECEBER'], errors='coerce')
        total_a_receber_por_fundacao = total_a_receber_por_fundacao.sort_values(by='SALDO_A_RECEBER', ascending=False)
        
        fig_bar_fundacao, ax_bar_fundacao = plt.subplots(figsize=(3, 2))
        ax_bar_fundacao.bar(
            total_a_receber_por_fundacao['FUNDAÇÃO'],
            total_a_receber_por_fundacao['SALDO_A_RECEBER'],
            color=colors_palette[1]
        )
        ax_bar_fundacao.set_ylabel('Valor total a receber', fontsize=5)
        ax_bar_fundacao.set_xlabel('Fundação', fontsize=5)
        for i, v in enumerate(total_a_receber_por_fundacao['SALDO_A_RECEBER']):
            num_val = float(v)
            ax_bar_fundacao.text(i, num_val + 10000, f'R${num_val:,.0f}', ha='center', va='bottom', fontsize=5)
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_fundacao, use_container_width=False)
    
    # Gráfico de barras - Distribuição de Valor a Receber por Tipo de Serviço
    with row1_col2:
        st.subheader('Valor a Receber por Tipo de Serviço')
        col_date, col_fundacao = st.columns(2)
        with col_date:
            datas_disponiveis_tipo = sorted(data['DATA'].unique())
            datas_selecionadas_tipo = st.multiselect("Data:", datas_disponiveis_tipo, default=[], key="data_tipo")
        with col_fundacao:
            fundacoes_disponiveis_tipo = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas_tipo = st.multiselect("Fundação:", fundacoes_disponiveis_tipo, default=[], key="fundacao_tipo")
        
        dados_local_tipo = data.copy()
        if datas_selecionadas_tipo:
            dados_local_tipo = dados_local_tipo[dados_local_tipo['DATA'].isin(datas_selecionadas_tipo)]
        if fundacoes_selecionadas_tipo:
            dados_local_tipo = dados_local_tipo[dados_local_tipo['FUNDAÇÃO'].isin(fundacoes_selecionadas_tipo)]
        
        dados_local_tipo['SALDO_A_RECEBER'] = saldo_receber_temp
        total_a_receber_por_tipo = dados_local_tipo.groupby('TIPO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_tipo['SALDO_A_RECEBER'] = pd.to_numeric(total_a_receber_por_tipo['SALDO_A_RECEBER'], errors='coerce')
        total_a_receber_por_tipo = total_a_receber_por_tipo.sort_values(by='SALDO_A_RECEBER', ascending=False)
        
        fig_bar_tipo, ax_bar_tipo = plt.subplots(figsize=(3, 2))
        ax_bar_tipo.bar(
            total_a_receber_por_tipo['TIPO'],
            total_a_receber_por_tipo['SALDO_A_RECEBER'],
            color=colors_palette[0]
        )
        ax_bar_tipo.set_ylabel('Valor total a receber', fontsize=5)
        ax_bar_tipo.set_xlabel('Tipo de Serviço', fontsize=5)
        for i, v in enumerate(total_a_receber_por_tipo['SALDO_A_RECEBER']):
            num_val = float(v)
            ax_bar_tipo.text(i, num_val + 10000, f'R${num_val:,.0f}', ha='center', va='bottom', fontsize=5)
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_tipo, use_container_width=False)
