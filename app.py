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
import openpyxl
import tempfile
import re
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io




# Carregar flat logo via URL direta
logo_flat = 'https://www.innovatismc.com.br/wp-content/uploads/2023/12/logo-innovatis-flatico-150x150.png'
st.set_page_config(layout="wide", page_title='DASHBOARD v1.2', page_icon=logo_flat)

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
st.title('Dashboard Financeiro (v1.2)')

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
    authenticator.logout("Logout", "main", key="logout_sidebar")
    st.write(f"Bem-vindo, {st.session_state['name']}!")
elif st.session_state["authentication_status"] is False:
    st.error('Usuário/Senha inválido')
elif st.session_state["authentication_status"] is None:
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
    s3 = boto3.resource(
        service_name='s3',
        region_name='us-east-2',
        aws_access_key_id='AKIA47GB733YQT2N7HNC',
        aws_secret_access_key='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'
    )

    # ---------------------------------------------------
    # Função para baixar a planilha Excel exportada do Google Sheets
    # ---------------------------------------------------
    @st.cache_data
    def baixar_planilha_excel():
        # Baixar a chave JSON diretamente do S3
        obj = s3.Bucket('jsoninnovatis').Object('chave2.json').get()
        creds_json = json.loads(obj['Body'].read().decode('utf-8'))
        
        # Definir os escopos para acesso ao Google Drive e leitura da planilha
        scope = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets.readonly'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        
        # Conectar via gspread para abrir a planilha e obter seu file ID
        client = gspread.authorize(creds)
        planilha = client.open("Cópia de Valores a Rebecer Innovatis - Fundações (12)")
        file_id = planilha.id  # Obtém o ID da planilha
        
        # Conectar à API do Google Drive para exportar a planilha como XLSX
        drive_service = build('drive', 'v3', credentials=creds)
        request = drive_service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        # Salva o conteúdo em um arquivo temporário com extensão .xlsx
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        with open(temp_file.name, "wb") as f:
            f.write(fh.getvalue())
        return temp_file.name

    # ---------------------------------------------------
    # Baixar a planilha Excel exportada do Google Sheets
    # ---------------------------------------------------
    arquivo = baixar_planilha_excel()
    # ---------------------------------------------------
    # Pré-processamento com openpyxl para tratar células mescladas
    # ---------------------------------------------------
    wb = openpyxl.load_workbook(arquivo, data_only=True)
    sheets_to_process = [
        sheet for sheet in wb.sheetnames 
        if sheet.strip().upper() not in ["GERAL_PROJETOS_FADEX", "TEDS SEM CONTRATO"]
    ]
    for sheet in sheets_to_process:
        ws = wb[sheet]
        merged_ranges = list(ws.merged_cells.ranges)
        for merged_range in merged_ranges:
            min_col, min_row, max_col, max_row = merged_range.bounds
            top_left_value = ws.cell(row=min_row, column=min_col).value
            ws.unmerge_cells(str(merged_range))
            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    ws.cell(row=row, column=col).value = top_left_value

    # Salva o workbook modificado em um novo arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(temp_file.name)
    temp_file.close()
    arquivo = temp_file.name  # Atualiza o caminho para o arquivo tratado

    # ---------------------------------------------------
    # Continuação do seu código original para processar o Excel
    # ---------------------------------------------------

    df_raw = pd.read_excel(arquivo, sheet_name=None)  # Carrega todas as abas do Excel tratado
    # A exibição dos dados do Google Sheets foi desativada:
    # st.write("Dados consolidados do Google Sheets:")
    # st.dataframe(df_raw)


    # Formatação para exibição dos floats com duas casas decimais
    pd.options.display.float_format = '{:.2f}'.format
    # ---------------------------------------------------
    # Função para limpar valores monetários
    # ---------------------------------------------------
    def clean_numeric(x):
        try:
            if pd.isna(x) or x == "":
                return 0
            x_str = str(x)
            cleaned = re.sub(r"[^\d\.,-]", "", x_str)
            if "," in cleaned:
                cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except Exception:
            return 0

    # ---------------------------------------------------
    # Função para carregar dados de desvio
    # ---------------------------------------------------
    @st.cache_data
    def carregar_dados_desvio():
        xls = pd.ExcelFile(arquivo)
        paginas_processar = [
            pagina for pagina in xls.sheet_names 
            if pagina.strip().upper() not in ["GERAL_PROJETOS_FADEX", "TEDS SEM CONTRATO"]
        ]
        
        lista_dfs = []
        cols_interesse = [
            "QUANT.", "CLIENTE", "PROJETO", "VALOR DO CONTRATO", 
            "REPASSE RECEBIDO", "CUSTOS INCORRIDOS", "VALOR",         
            "OUTROS CORRELATOS", "VALOR2", "SALDO A RECEBER",
        ]

        for pagina in paginas_processar:
            df = pd.read_excel(arquivo, sheet_name=pagina, skiprows=3)
            df.columns = df.columns.str.strip().str.upper().str.replace("  ", " ")
            
            if "PROJETO/FIN." in df.columns:
                df.rename(columns={"PROJETO/FIN.": "PROJETO"}, inplace=True)
            if "PROJETO/OBJETO" in df.columns:
                df.rename(columns={"PROJETO/OBJETO": "PROJETO"}, inplace=True)
            
            missing = [col for col in cols_interesse if col not in df.columns]
            if missing:
                continue
                
            df = df[cols_interesse]
            df = df.replace(r'^\s*$', pd.NA, regex=True)
            df = df.dropna(subset=["QUANT."])
            
            for col in ["VALOR DO CONTRATO", "REPASSE RECEBIDO", "CUSTOS INCORRIDOS", 
                       "VALOR", "OUTROS CORRELATOS", "VALOR2"]:
                df[col] = df[col].fillna(0).apply(clean_numeric)

            df = df[df["SALDO A RECEBER"] > 0]
            df['PAGINA'] = pagina
            lista_dfs.append(df)

        df_consolidado = pd.concat(lista_dfs, ignore_index=True)
        df_consolidado['PROJECT_ID'] = pd.factorize(
            df_consolidado[['QUANT.', 'CLIENTE', 'PROJETO']].apply(lambda row: '_'.join(row.astype(str)), axis=1)
        )[0] + 1
        
        return df_consolidado

    # ---------------------------------------------------
    # Carregar planilha original
    # ---------------------------------------------------
    @st.cache_data
    def carregar_planilha():
        obj = s3.Bucket('jsoninnovatis').Object('chave2.json').get()
        creds_json = json.loads(obj['Body'].read().decode('utf-8'))
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        planilha = client.open("AJUSTADA - Valores a receber Innovatis").worksheet("VALORES A RECEBER")
        st.write("Conectado à planilha com sucesso!")
        dados = planilha.get_all_records()
        df = pd.DataFrame(dados)
        return df

    @st.cache_data
    def preprocess_data(df):
        df.columns = df.columns.str.strip().str.replace(' ', '_')
        data = df[['FUNDAÇÃO', 'CLIENTE', 'TIPO', 'PREVISÃO_DE_RECEBIMENTO', 'ANO',
                   'SALDO_A_RECEBER', 'CUSTOS_INCORRIDOS', 'OUTROS_E_CORRELATOS']].copy()
        data = data.rename(columns={'OUTROS_E_CORRELATOS': 'CUSTOS_CORRELATOS'})
        
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
        
        # Não excluímos mais nenhuma data
        data['TIPO'] = data['TIPO'].replace({'PROJETO/Empresa Privada': 'PROJETO'})
       
        
        for col in ['CUSTOS_INCORRIDOS', 'CUSTOS_CORRELATOS']:
            data[col] = (data[col].str.strip()
                         .str.replace('R\$', '', regex=True)
                         .str.replace('.', '')
                         .str.replace(',', '.'))
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data

    @st.cache_data
    def load_data(nrows):
        return data.head(nrows)

    @st.cache_data
    def load_logo():
        logo_obj = s3.Bucket('jsoninnovatis').Object('Logo.png').get()
        logo_data = logo_obj['Body'].read()
        return Image.open(BytesIO(logo_data))

    # Carregar dados
    data_load_state = st.text('Carregando dados...')
    
    # Carregar dados originais
    df_raw = carregar_planilha()
    data = preprocess_data(df_raw)
    data = load_data(10000)
    
    # Carregar dados para análise de desvio
    df_desvio = carregar_dados_desvio()
    
    data_load_state.text('Carregamento de dados concluído!')

    # Carregar e exibir logo
    logo_image = load_logo()
    st.sidebar.image(logo_image, use_container_width=True)
    
    # Estilização
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
            
            /* Botões com fundo branco e detalhes verdes */
            .stButton > button {
                background-color: white !important;
                color: rgb(49, 170, 77) !important;
                border-color: rgb(49, 170, 77) !important;
                border-width: 1px !important;
                border-style: solid !important;
                font-weight: 500 !important;
            }
            .stButton > button:hover {
                background-color: rgba(49, 170, 77, 0.1) !important;
                border-color: rgb(49, 170, 77) !important;
            }
            .stButton > button:active {
                background-color: rgba(49, 170, 77, 0.2) !important;
            }
            
            
            /* Ajuste apenas para a barra do slider e seus valores */
            [data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stThumbValue"] {
                color: rgb(49, 170, 77) !important;
                background-color: transparent !important;
                border: none !important;
            }
            
            [data-testid="stSlider"] [data-baseweb="slider-track"] {
                background-color: rgba(49, 170, 77, 0.2) !important;
            }
            
            [data-testid="stSlider"] [data-baseweb="slider-track-fill"] {
                background-color: rgb(49, 170, 77) !important;
            }
            
            [data-testid="stSlider"] [data-baseweb="slider-thumb"] {
                background-color: rgb(49, 170, 77) !important;
            }
            
            /* Valores do slider (que estão em vermelho) */
            [data-testid="stSlider"] span {
                color: rgb(49, 170, 77) !important;
            }
            
            /* Texto do slider */
            [data-testid="stSlider"] p {
                color: rgb(49, 170, 77) !important;
            }
            
            /* Multiselect e selectbox */
            .stMultiSelect > div > div > div {
                border-color: rgb(49, 170, 77) !important;
            }
            .stMultiSelect > div > div > div:hover {
                border-color: rgb(39, 150, 67) !important;
            }
            .stMultiSelect > div[data-baseweb="tag"] {
                background-color: rgb(49, 170, 77) !important;
            }
            
            /* Tabs e outros elementos de navegação */
            .stTabs [data-baseweb="tab-list"] {
                border-bottom-color: rgb(49, 170, 77) !important;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                color: rgb(49, 170, 77) !important;
                border-bottom-color: rgb(49, 170, 77) !important;
            }
            
            /* Progress bar */
            .stProgress > div > div > div > div {
                background-color: rgb(49, 170, 77) !important;
            }
            
            /* Métricas */
            .stMetric > div[data-testid="stMetricDelta"] > div {
                color: rgb(49, 170, 77) !important;
            }
            
            /* Cores de links */
            a {
                color: rgb(49, 170, 77) !important;
            }
            a:hover {
                color: rgb(39, 150, 67) !important;
            }
            
            /* Cores de foco */
            :focus {
                outline-color: rgb(49, 170, 77) !important;
            }
            
            /* Cores de seleção */
            ::selection {
                background-color: rgba(49, 170, 77, 0.3) !important;
            }
            
            /* Cores para elementos de data input */
            input[type="date"] {
                color: rgb(49, 170, 77) !important;
            }
            
            /* Cores para tooltips */
            [data-testid="stTooltipIcon"] path {
                fill: rgb(49, 170, 77) !important;
            }

            /* Corrigir cor de fundo dos campos de seleção */
            .stSelectbox > div > div,
            .stMultiSelect > div > div {
                background-color: white !important;
            }

            /* Manter apenas a borda verde */
            .stSelectbox > div > div[data-baseweb="select"] {
                border-color: #31aa4d !important;
                background-color: white !important;
            }

            /* Corrigir cor de fundo do dropdown quando aberto */
            .stSelectbox > div > div > div {
                background-color: white !important;
            }

            /* Corrigir cor de hover nas opções */
            .stSelectbox > div > div > div:hover {
                background-color: rgba(49, 170, 77, 0.1) !important;
            }

            /* Corrigir cor de fundo do slider */
            .stSlider > div > div > div {
                background-color: white !important;
            }
                
            .stSlider > div > div > div {
                background-color: #ffffff00 !important;
            }
                
            /* Corrigir cor do texto do slider */
            [data-testid="stSlider"] > div > div > div > p {
                color: rgb(49, 51, 63) !important;  /* Cor padrão do texto do Streamlit */
            }
            
            /* Manter apenas os valores em verde */
            [data-testid="stSlider"] [data-testid="stThumbValue"] {
                color: rgb(49, 170, 77) !important;
            }
                
            [data-testid="stSlider"] p {
                color: rgb(49, 51, 63) !important;
            }
            
        </style>
    """, unsafe_allow_html=True)
    
    # Filtros interativos
    st.sidebar.header('Filtros:')
    
    # Função auxiliar para ordenar meses no formato MM/AAAA
    def ordenar_datas(datas):
        # Filtrar apenas datas válidas (no formato MM/AAAA)
        datas_validas = [d for d in datas if d != 'A definir' and re.match(r'^\d{2}/\d{4}$', d)]
        # Converter para objetos datetime para ordenação
        datas_dt = [pd.to_datetime(d, format='%m/%Y') for d in datas_validas]
        # Criar dicionário para mapear datas string para objetos datetime
        data_map = dict(zip(datas_validas, datas_dt))
        # Ordenar as datas válidas
        datas_ordenadas = sorted(datas_validas, key=lambda d: data_map[d])
        # Adicionar 'A definir' ao final, se existir
        if 'A definir' in datas:
            datas_ordenadas.append('A definir')
        return datas_ordenadas
    
    # Armazenar os filtros em variáveis temporárias
    meses_disponiveis = ordenar_datas(data['DATA'].unique())
    meses_temp = st.sidebar.multiselect('Meses:', meses_disponiveis)
    tipos_temp = st.sidebar.multiselect('Tipos de Serviço:', data['TIPO'].unique())
    fundacoes_temp = st.sidebar.multiselect('Fundações:', data['FUNDAÇÃO'].unique())
    clientes_temp = st.sidebar.multiselect('Clientes:', data['CLIENTE'].unique())
    
    saldo_receber_temp = (data['SALDO_A_RECEBER']
                          .str.strip()
                          .str.replace('R$', '')
                          .str.replace('.', '')
                          .str.replace(',', '.'))
    saldo_receber_temp = pd.to_numeric(saldo_receber_temp, errors='coerce')
    
    min_saldo_temp, max_saldo_temp = st.sidebar.slider(
        'Selecione o intervalo:',
        min_value=float(saldo_receber_temp.min()),
        max_value=float(saldo_receber_temp.max()),
        value=(float(saldo_receber_temp.min()), float(saldo_receber_temp.max())),
        step=1000.0,
        format="R$ %.2f"  # Formato correto: R$ com ponto decimal
    )
    
    # Inicializar os filtros na sessão se ainda não existirem
    if 'meses' not in st.session_state:
        st.session_state.meses = []
    if 'tipos' not in st.session_state:
        st.session_state.tipos = []
    if 'fundacoes' not in st.session_state:
        st.session_state.fundacoes = []
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    if 'min_saldo' not in st.session_state:
        st.session_state.min_saldo = float(saldo_receber_temp.min())
    if 'max_saldo' not in st.session_state:
        st.session_state.max_saldo = float(saldo_receber_temp.max())
    
    # Criar colunas para centralizar os botões
    col1, col2, col3 = st.sidebar.columns([1,2,1])
    
    # Botão para aplicar os filtros
    with col2:
        if st.button('Filtrar', use_container_width=True):
            st.session_state.meses = meses_temp
            st.session_state.tipos = tipos_temp
            st.session_state.fundacoes = fundacoes_temp
            st.session_state.clientes = clientes_temp
            st.session_state.min_saldo = min_saldo_temp
            st.session_state.max_saldo = max_saldo_temp
            st.rerun()  # Método atualizado para recarregar a página
    
    # Usar os filtros armazenados na sessão para filtrar os dados
    filtered_data = data.copy()
    if st.session_state.meses:
        filtered_data = filtered_data[filtered_data['DATA'].isin(st.session_state.meses)]
    if st.session_state.tipos:
        filtered_data = filtered_data[filtered_data['TIPO'].isin(st.session_state.tipos)]
    if st.session_state.fundacoes:
        filtered_data = filtered_data[filtered_data['FUNDAÇÃO'].isin(st.session_state.fundacoes)]
    if st.session_state.clientes:
        filtered_data = filtered_data[filtered_data['CLIENTE'].isin(st.session_state.clientes)]
    
    filtered_data['SALDO_A_RECEBER'] = saldo_receber_temp
    filtered_data = filtered_data[(filtered_data['SALDO_A_RECEBER'] >= st.session_state.min_saldo) &
                                  (filtered_data['SALDO_A_RECEBER'] <= st.session_state.max_saldo)]
    
    # Botão para limpar todos os filtros
    with col2:
        if st.button('Limpar', use_container_width=True):
            st.session_state.meses = []
            st.session_state.tipos = []
            st.session_state.fundacoes = []
            st.session_state.clientes = []
            st.session_state.min_saldo = float(saldo_receber_temp.min())
            st.session_state.max_saldo = float(saldo_receber_temp.max())
            st.rerun()  # Método atualizado para recarregar a página
    
    st.sidebar.subheader('Resumo dos Filtros:')
    st.sidebar.write('Número de linhas:', filtered_data.shape[0])
    total_a_receber_filtrado = filtered_data['SALDO_A_RECEBER'].sum()
    total_a_receber_filtrado_real = f'R$ {total_a_receber_filtrado:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    st.sidebar.write('Valor Total a Receber:', total_a_receber_filtrado_real)
    
    st.subheader('Valor Total a Receber pela Empresa:')
    st.write(f'<p style="font-size:40px">{total_a_receber_filtrado_real}</p>', unsafe_allow_html=True)
    
    # Modificar o checkbox para um botão com o mesmo estilo
    if st.button('Mostrar Planilha Filtrada', key='btn_mostrar_planilha'):
        st.markdown("<h3 style='font-size:140%;'>Planilha de Contas a Receber - Higienizada em tempo real</h3>", unsafe_allow_html=True)
        
        st.info("""
        Esta tabela mostra todos os registros de contas a receber aplicando os filtros selecionados no painel lateral.
        """)
        
        # Preparar os dados para exibição formatada
        df_exibir = filtered_data.copy()
        
        # Converter a coluna SALDO_A_RECEBER para numérico se ainda não estiver
        if not pd.api.types.is_numeric_dtype(df_exibir['SALDO_A_RECEBER']):
            df_exibir['SALDO_A_RECEBER'] = pd.to_numeric(df_exibir['SALDO_A_RECEBER'], errors='coerce')
        
        # Aplicar formatação monetária usando o mesmo padrão da tabela de desvios
        st.dataframe(
            df_exibir.style.format({
                'SALDO_A_RECEBER': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                'CUSTOS_INCORRIDOS': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                'CUSTOS_CORRELATOS': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
            }, decimal=',', thousands='.'),
            use_container_width=True
        )
        
        st.markdown(f"<p style='font-size:140%;'>Tamanho da amostra: {filtered_data.shape[0]}</p>", unsafe_allow_html=True)

    # Dashboard de Alerta para Saldos em Atraso
    st.markdown("---")
    st.subheader("Pagamentos em Atraso ⚠️")
    
    # Obter mês atual
    mes_atual = datetime.datetime.now().strftime('%m/%Y')
    
    # Converter as datas para datetime para comparação
    data_copy = data.copy()
    
    # Filtrar apenas os registros com data válida (não 'A definir')
    data_copy = data_copy[data_copy['DATA'] != 'A definir']
    
    # Converter coluna DATA para datetime para comparação
    try:
        data_copy['DATA_DT'] = pd.to_datetime(data_copy['DATA'], format='%m/%Y', errors='coerce')
        mes_atual_dt = pd.to_datetime(mes_atual, format='%m/%Y')
        
        # Encontrar registros com data anterior ao mês atual
        registros_atrasados = data_copy[data_copy['DATA_DT'] < mes_atual_dt]
        
        # Converter SALDO_A_RECEBER para numérico se ainda não estiver
        registros_atrasados['SALDO_A_RECEBER'] = pd.to_numeric(
            registros_atrasados['SALDO_A_RECEBER'].str.strip()
            .str.replace('R$', '')
            .str.replace('.', '')
            .str.replace(',', '.'),
            errors='coerce'
        )
        
        # Filtrar apenas registros com saldo maior que zero
        registros_atrasados = registros_atrasados[registros_atrasados['SALDO_A_RECEBER'] > 0]
        
        # Calcular o total atrasado
        total_atrasado = registros_atrasados['SALDO_A_RECEBER'].sum()
        total_atrasado_formatado = f'R$ {total_atrasado:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        
        # Verificar se existem registros atrasados
        if len(registros_atrasados) > 0:
            # Criar duas colunas para exibir métricas
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label=f"Registros com saldo a receber vencidos (antes de {mes_atual})", 
                    value=len(registros_atrasados)
                )
            
            with col2:
                st.metric(
                    label="Valor total em atraso", 
                    value=total_atrasado_formatado
                )
            
            # Botão para mostrar detalhes dos registros atrasados
            if st.button("Mostrar Registros em Atraso"):
                # Preparar dataframe para exibição formatada
                df_atrasados_exibir = registros_atrasados.copy()
                
                st.info("""
                Esta tabela apresenta todos os registros com prazos de recebimento vencidos, ou seja, 
                valores que deveriam ter sido recebidos em meses anteriores e ainda não foram quitados. 
                A coluna "ATRASO_MESES" indica há quantos meses o pagamento está pendente, permitindo 
                priorizar as cobranças mais antigas.
                """)
                
                # Ordenar por data (mais antigo primeiro)
                df_atrasados_exibir = df_atrasados_exibir.sort_values(by='DATA_DT')
                
                # Calcular atraso em meses
                def calcular_meses_atraso(data_registro):
                    if pd.isnull(data_registro):
                        return 0
                    delta = (mes_atual_dt.year - data_registro.year) * 12 + (mes_atual_dt.month - data_registro.month)
                    return delta
                
                # Aplicar função para calcular atraso em meses
                df_atrasados_exibir['ATRASO_MESES'] = df_atrasados_exibir['DATA_DT'].apply(calcular_meses_atraso)
                
                # Selecionar e reordenar colunas relevantes
                colunas_exibir = ['DATA', 'CLIENTE', 'FUNDAÇÃO', 'TIPO', 'SALDO_A_RECEBER', 'ATRASO_MESES']
                df_atrasados_exibir = df_atrasados_exibir[colunas_exibir]
                
                # Formatar o dataframe para exibição
                st.dataframe(
                    df_atrasados_exibir.style.format({
                        'SALDO_A_RECEBER': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                        'ATRASO_MESES': lambda x: f"{int(x)} {'mês' if int(x) == 1 else 'meses'}"
                    }, decimal=',', thousands='.'),
                    use_container_width=True
                )
        else:
            st.success("Não há registros com saldo a receber em atraso! Todos os valores estão dentro do prazo.")
    except Exception as e:
        st.error(f"Erro ao processar alertas: {str(e)}")
        st.info("Verifique se o formato das datas está correto (MM/AAAA).")

    # Dashboard de Desvio de Proporção
    st.markdown("---")
    st.subheader("Desvio na Proporção dos Repasses 🔍")

    # Calcular métricas de desvio
    tolerance = 20.0
    df_desvio['PROP_REPASSE'] = df_desvio.apply(
        lambda row: row['REPASSE RECEBIDO'] / row['VALOR DO CONTRATO']
        if row['REPASSE RECEBIDO'] and row['VALOR DO CONTRATO'] != 0 else np.nan, axis=1)

    df_desvio['EXPECTED_VALOR'] = df_desvio.apply(
        lambda row: row['CUSTOS INCORRIDOS'] * row['PROP_REPASSE']
        if pd.notna(row['PROP_REPASSE']) and row['CUSTOS INCORRIDOS'] != 0 else np.nan, axis=1)

    df_desvio['EXPECTED_VALOR2'] = df_desvio.apply(
        lambda row: row['OUTROS CORRELATOS'] * row['PROP_REPASSE']
        if pd.notna(row['PROP_REPASSE']) and row['OUTROS CORRELATOS'] != 0 else np.nan, axis=1)

    df_desvio['EXPECTED_VALOR_RND'] = df_desvio['EXPECTED_VALOR'].round(2)
    df_desvio['EXPECTED_VALOR2_RND'] = df_desvio['EXPECTED_VALOR2'].round(2)
    df_desvio['VALOR_RND'] = df_desvio['VALOR'].round(2)
    df_desvio['VALOR2_RND'] = df_desvio['VALOR2'].round(2)

    df_desvio['DESVIO_VALOR'] = df_desvio.apply(
        lambda row: True if (pd.notna(row['EXPECTED_VALOR_RND']) and 
                          (row['EXPECTED_VALOR_RND'] - row['VALOR_RND'] > tolerance))
                    else False, axis=1)

    df_desvio['DESVIO_VALOR2'] = df_desvio.apply(
        lambda row: True if (pd.notna(row['EXPECTED_VALOR2_RND']) and 
                          (row['EXPECTED_VALOR2_RND'] - row['VALOR2_RND'] > tolerance))
                    else False, axis=1)

    df_desvio['DESVIO_PROPORCAO'] = df_desvio['DESVIO_VALOR'] | df_desvio['DESVIO_VALOR2']

    # Calcular o desvio em reais somando as diferenças dos dois tipos
    df_desvio['DESVIO_VALOR_REAIS'] = df_desvio.apply(
        lambda row: (row['EXPECTED_VALOR_RND'] - row['VALOR_RND']) 
        if pd.notna(row['EXPECTED_VALOR_RND']) and pd.notna(row['VALOR_RND']) else 0, axis=1
    )
    
    df_desvio['DESVIO_VALOR2_REAIS'] = df_desvio.apply(
        lambda row: (row['EXPECTED_VALOR2_RND'] - row['VALOR2_RND']) 
        if pd.notna(row['EXPECTED_VALOR2_RND']) and pd.notna(row['VALOR2_RND']) else 0, axis=1
    )
    
    # Somar os dois tipos de desvio para obter o desvio total em reais
    df_desvio['DESVIO_EM_REAIS'] = df_desvio['DESVIO_VALOR_REAIS'] + df_desvio['DESVIO_VALOR2_REAIS']
    
    # Garantir que registros com valor total do desvio igual a zero reais não entrem no modelo
    df_desvio.loc[df_desvio['DESVIO_EM_REAIS'] <= 0, 'DESVIO_PROPORCAO'] = False
    
    # Nova lógica: verificar desvios por bloco de projeto
    # Este cálculo corrige casos onde múltiplas linhas do mesmo projeto podem parecer em desvio
    # individualmente, mas quando analisadas em conjunto (como um bloco) estão corretas.
    # Exemplo: Um projeto com dois repasses (33% e 34%) pode ter múltiplos pagamentos distribuídos
    # que não correspondem linha a linha, mas que no total representam a proporção correta.
    df_desvio_por_projeto = df_desvio.copy()
    
    # Agrupar por projeto para somar valores de múltiplas linhas do mesmo projeto
    projeto_totals = df_desvio_por_projeto.groupby(['QUANT.', 'CLIENTE', 'PROJETO']).agg({
        'REPASSE RECEBIDO': 'sum',
        'VALOR DO CONTRATO': 'first',  # Assume que é o mesmo para todas as linhas do projeto
        'CUSTOS INCORRIDOS': 'first',  # Assume que é o mesmo para todas as linhas do projeto
        'VALOR': 'sum',                # Soma todos os valores recebidos para este projeto
        'OUTROS CORRELATOS': 'first',  # Assume que é o mesmo para todas as linhas do projeto
        'VALOR2': 'sum',               # Soma todos os valores correlatos recebidos
        'PROJECT_ID': 'first'          # Identificador único do projeto
    }).reset_index()
    
    # Recalcular a proporção e desvios a nível de projeto agrupado
    projeto_totals['PROP_REPASSE_GRUPO'] = projeto_totals.apply(
        lambda row: row['REPASSE RECEBIDO'] / row['VALOR DO CONTRATO'] 
        if row['VALOR DO CONTRATO'] > 0 else 0, axis=1
    )
    
    projeto_totals['EXPECTED_VALOR_GRUPO'] = projeto_totals.apply(
        lambda row: row['CUSTOS INCORRIDOS'] * row['PROP_REPASSE_GRUPO'] 
        if row['PROP_REPASSE_GRUPO'] > 0 else 0, axis=1
    )
    
    projeto_totals['EXPECTED_VALOR2_GRUPO'] = projeto_totals.apply(
        lambda row: row['OUTROS CORRELATOS'] * row['PROP_REPASSE_GRUPO'] 
        if row['PROP_REPASSE_GRUPO'] > 0 else 0, axis=1
    )
    
    # Arredondar para comparação consistente
    projeto_totals['EXPECTED_VALOR_RND_GRUPO'] = projeto_totals['EXPECTED_VALOR_GRUPO'].round(2)
    projeto_totals['EXPECTED_VALOR2_RND_GRUPO'] = projeto_totals['EXPECTED_VALOR2_GRUPO'].round(2)
    projeto_totals['VALOR_RND_GRUPO'] = projeto_totals['VALOR'].round(2)
    projeto_totals['VALOR2_RND_GRUPO'] = projeto_totals['VALOR2'].round(2)
    
    # Calcular desvios a nível de grupo
    projeto_totals['DESVIO_VALOR_GRUPO'] = projeto_totals.apply(
        lambda row: True if (pd.notna(row['EXPECTED_VALOR_RND_GRUPO']) and 
                          (row['EXPECTED_VALOR_RND_GRUPO'] - row['VALOR_RND_GRUPO'] > tolerance))
                    else False, axis=1
    )
    
    projeto_totals['DESVIO_VALOR2_GRUPO'] = projeto_totals.apply(
        lambda row: True if (pd.notna(row['EXPECTED_VALOR2_RND_GRUPO']) and 
                          (row['EXPECTED_VALOR2_RND_GRUPO'] - row['VALOR2_RND_GRUPO'] > tolerance))
                    else False, axis=1
    )
    
    # Flag de desvio a nível de grupo
    projeto_totals['DESVIO_PROPORCAO_GRUPO'] = projeto_totals['DESVIO_VALOR_GRUPO'] | projeto_totals['DESVIO_VALOR2_GRUPO']
    
    # Corrigir o desvio no dataframe original com base na análise por grupo
    # Se um projeto não tem desvio no nível agrupado, corrigir o flag de desvio para todas as suas linhas
    for idx, row in projeto_totals.iterrows():
        if not row['DESVIO_PROPORCAO_GRUPO']:
            # Selecionar todas as linhas deste projeto no dataframe original
            projeto_mask = (df_desvio['QUANT.'] == row['QUANT.']) & \
                          (df_desvio['CLIENTE'] == row['CLIENTE']) & \
                          (df_desvio['PROJETO'] == row['PROJETO'])
            
            # Desativar flag de desvio para todas as linhas deste projeto
            df_desvio.loc[projeto_mask, 'DESVIO_PROPORCAO'] = False
            
            # Também zerar o valor do desvio monetário para essas linhas
            df_desvio.loc[projeto_mask, 'DESVIO_VALOR_REAIS'] = 0
            df_desvio.loc[projeto_mask, 'DESVIO_VALOR2_REAIS'] = 0
            df_desvio.loc[projeto_mask, 'DESVIO_EM_REAIS'] = 0
    
    # Exibir métricas do dashboard de desvio
    total_registros = len(df_desvio)
    registros_com_desvio = df_desvio['DESVIO_PROPORCAO'].sum()
    percentual_conformidade = ((total_registros - registros_com_desvio) / total_registros) * 100

    # Criando layout com 5 colunas para melhor distribuição visual
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(label="Total de Registros", value=total_registros)
    with col2:
        st.metric(label="Registros com Desvio", value=int(registros_com_desvio))
    with col3:
        st.metric(label="Conformidade", value=f"{percentual_conformidade:.1f}%")
    with col4:
        st.metric(label="Desvio Total", value=f"R$ {df_desvio['DESVIO_EM_REAIS'].sum():,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'))
    with col5:
        desvio_medio = df_desvio.loc[df_desvio['DESVIO_PROPORCAO'], 'DESVIO_EM_REAIS'].mean()
        valor_formatado = f"R$ {desvio_medio:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.').replace('_', '.') if not np.isnan(desvio_medio) else "R$ 0,00"
        st.metric(label="Desvio Médio", value=valor_formatado)


    # Botão para mostrar registros com desvio de proporção
    if st.button("Mostrar Registros com Desvio de Proporção"):
        # Remover checkbox e todo código relacionado
        st.info("""
        Esta tabela mostra projetos onde há um descompasso financeiro entre o que a fundação recebeu e o que 
        foi repassado à Innovatis. Quando a fundação recebe 60% do valor do contrato, por exemplo, nossa 
        empresa deveria receber cerca de 60% dos valores previstos. Quando isso não acontece, significa que 
        há dinheiro que deveria ter sido repassado, mas não foi.
        """)
        
        # Filtrar apenas os registros que têm desvio após a análise por bloco
        df_com_desvio = df_desvio[df_desvio['DESVIO_PROPORCAO'] == True].copy()

        # Calcular o desvio total somando as diferenças de ambos os tipos de NF
        df_com_desvio['DESVIO_INCORRIDOS'] = df_com_desvio.apply(
            lambda row: (row['EXPECTED_VALOR_RND'] - row['VALOR_RND']) 
            if pd.notna(row['EXPECTED_VALOR_RND']) and pd.notna(row['VALOR_RND']) else 0, axis=1
        )

        df_com_desvio['DESVIO_CORRELATOS'] = df_com_desvio.apply(
            lambda row: (row['EXPECTED_VALOR2_RND'] - row['VALOR2_RND']) 
            if pd.notna(row['EXPECTED_VALOR2_RND']) and pd.notna(row['VALOR2_RND']) else 0, axis=1
        )

        # Somar os dois tipos de desvio para obter o desvio total
        df_com_desvio['DESVIO_EM_REAIS'] = df_com_desvio['DESVIO_INCORRIDOS'] + df_com_desvio['DESVIO_CORRELATOS']

        # Filtrar para remover registros com desvio total igual a zero
        df_com_desvio = df_com_desvio[df_com_desvio['DESVIO_EM_REAIS'] > 0]

        if not df_com_desvio.empty:
            # Adicionar informação sobre a proporção no nível do projeto
            # Mapear a proporção de repasse por projeto para cada linha
            projeto_prop_map = dict(zip(
                projeto_totals['PROJECT_ID'],
                projeto_totals['PROP_REPASSE_GRUPO']
            ))
            
            # Adicionar coluna com a proporção total do projeto
            df_com_desvio['PROP_PROJETO'] = df_com_desvio['PROJECT_ID'].map(projeto_prop_map)
            df_com_desvio['PROP_PROJETO'] = df_com_desvio['PROP_PROJETO'].fillna(0) * 100  # Converter para percentual
            
            # Converter PROP_REPASSE para percentual também
            df_com_desvio['PROP_REPASSE'] = df_com_desvio['PROP_REPASSE'] * 100
            
            # Selecionar e renomear colunas para exibição
            colunas_exibir = {
                'QUANT.': 'Quant.',
                'CLIENTE': 'Cliente',
                'PROJETO': 'Projeto',
                'PAGINA': 'Página de Origem',
                'PROP_REPASSE': '% Repasse na Linha',
                'PROP_PROJETO': '% Repasse do Projeto',
                'EXPECTED_VALOR_RND': 'NF Incorridos Esperada',
                'VALOR_RND': 'NF Incorridos Emitida',
                'EXPECTED_VALOR2_RND': 'NF Correlatos Esperado',
                'VALOR2_RND': 'NF Correlatos Emitida',
                'DESVIO_EM_REAIS': 'Desvio (R$)'
            }

            df_exibir = df_com_desvio[list(colunas_exibir.keys())].rename(columns=colunas_exibir)

            # Preencher valores vazios com 0
            df_exibir.fillna(0, inplace=True)

            # Exibir a tabela com os registros que têm desvio, formatando valores monetários corretamente
            st.subheader(f"Registros com Desvio de Proporção ({len(df_exibir)} encontrados)")
            st.dataframe(
                df_exibir.style.format({
                    'NF Incorridos Esperada': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                    'NF Incorridos Emitida': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                    'NF Correlatos Esperado': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                    'NF Correlatos Emitida': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                    'Desvio (R$)': lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                    '% Repasse na Linha': lambda x: f"{x:.1f}%",
                    '% Repasse do Projeto': lambda x: f"{x:.1f}%",
                    'Quant.': lambda x: f"{int(x)}"
                }, decimal=',', thousands='.'),
                use_container_width=True
            )
        else:
            st.info("Não foram encontrados registros com desvio de proporção.")



    # Adicionando espaço após as métricas
    st.markdown("---")
    
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
            datas_disponiveis = ordenar_datas(data['DATA'].unique())
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
            ax_bar.text(v + (v * 0.01), i, f'R$ {v:,.2f}M'.replace(',', '_').replace('.', ',').replace('_', '.'), va='center', fontsize=4, color='black')
        st.pyplot(fig_bar, use_container_width=False)
    
    # Gráfico de Pizza: Distribuição dos Custos Incorridos e Correlatos
    with row2_col2:
        st.subheader('Distribuição dos Custos')
        col1, col2, col3 = st.columns(3)
        with col1:
            datas_disponiveis_custos = ordenar_datas(data['DATA'].unique())
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
                return f'{pct:.1f}%\nR$ {val:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
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
            datas_disponiveis_fundacao = ordenar_datas(data['DATA'].unique())
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
            ax_bar_fundacao.text(i, num_val + 10000, f'R$ {num_val:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.'), 
                                ha='center', va='bottom', fontsize=5)
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
            datas_disponiveis_tipo = ordenar_datas(data['DATA'].unique())
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
            ax_bar_tipo.text(i, num_val + 10000, f'R$ {num_val:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.'), 
                            ha='center', va='bottom', fontsize=5)
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_tipo, use_container_width=False)


# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center;'>Dashboard Financeiro Versão 1.2 © 2025</div>", unsafe_allow_html=True)
