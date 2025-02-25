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
import json
import datetime
from io import BytesIO
from PIL import Image


#Carregar flat logo via URL direta
logo_flat = 'https://www.innovatismc.com.br/wp-content/uploads/2023/12/logo-innovatis-flatico-150x150.png'
st.set_page_config(layout="wide", page_title='DASHBOARD v1.0', page_icon=logo_flat)



# Importa a fonte Poppins do Google Fonts
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Aplica a fonte Poppins a todos os componentes */
        [class^=st-emotion] {
            font-family: 'Poppins', sans-serif !important;
        }

        /* Se necessário, você pode especificar um estilo diferente para o corpo */
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
    authenticator.logout()
    st.write(f"Bem-vindo, {st.session_state['name']}!")
    
elif st.session_state["authentication_status"] is False:
    st.error('Usuário/Senha is inválido')
if st.session_state["authentication_status"] is None:
    st.markdown(
        """
        <style>
        /* Quando não autenticado, definimos um max-width menor para o container principal */
        div[data-testid="stAppViewContainer"] {
            max-width: 600px; /* Ajuste conforme desejar */
            margin: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.warning('Por Favor, utilize seu usuário e senha!')
    
    # O resto do código só executa se autenticado
if st.session_state["authentication_status"]:
        
    
    # Função para baixar o arquivo de credenciais do Google Drive

    s3 = boto3.client('s3')

    s3 = boto3.resource(
        service_name='s3',
        region_name='us-east-2',
        aws_access_key_id='AKIA47GB733YQT2N7HNC',
        aws_secret_access_key='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'
    )


   # Baixar o arquivo JSON diretamente do S3
    obj = s3.Bucket('jsoninnovatis').Object('chave2.json').get()
    # Ler o conteúdo do objeto e decodificar para string, em seguida converter para dict
    creds_json = json.loads(obj['Body'].read().decode('utf-8'))


    # Definir o escopo de acesso para Google Sheets e Google Drive
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

	
    # Criar as credenciais a partir do JSON baixado
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    
    # Acessar a planilha do Google
    planilha = client.open("AJUSTADA - Valores a receber Innovatis").worksheet("VALORES A RECEBER")
    st.write("Conectado à planilha com sucesso!")
    
    
    # Obtenha todos os dados da planilha
    dados = planilha.get_all_records()
    
    # Converta os dados para um DataFrame
    df = pd.DataFrame(dados)

	
    #Jogando pro streamlit nossa tabela
    def load_data(nrows):
        data = df
        return data
    
    # Carregar os dados e mostrar um estado de carregamento
    data_load_state = st.text('Carregando dados...')
    data = load_data(10000)
    data_load_state.text('Carregamento de dados concluído!')
        
    # Renomear as colunas para remover espaços
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(' ', '_')
    
    # Selecionar variáveis de interesse
    data = df[['FUNDAÇÃO', 'CLIENTE', 'TIPO', 'PREVISÃO_DE_RECEBIMENTO', 'ANO', 'SALDO_A_RECEBER', 'CUSTOS_INCORRIDOS', 'OUTROS_E_CORRELATOS']]

    #Renomeie Outros e Correlatos para Custos Correlatos
    data = data.rename(columns={'OUTROS_E_CORRELATOS': 'CUSTOS_CORRELATOS'})
    
    
    # Transformar a coluna 'PREVISÃO_DE_RECEBIMENTO' e 'ANO' em uma coluna única 'DATA'
    data['PREVISÃO_DE_RECEBIMENTO'] = data['PREVISÃO_DE_RECEBIMENTO'].str.strip()
    data['PREVISÃO_DE_RECEBIMENTO'] = data['PREVISÃO_DE_RECEBIMENTO'].replace({'Janeiro': '01', 'JANEIRO': '01', 'Janeiro ': '01', 'JANEIRO ': '01', 'Fevereiro': '02', 'FEVEREIRO': '02', 'Fevereiro ': '02', 'FEVEREIRO ': '02', 'Março': '03', 'MARÇO': '03', 'Março ': '03', 'MARÇO ': '03', 'Abril': '04', 'ABRIL': '04', 'Abril ': '04', 'ABRIL ': '04', 'Maio': '05', 'MAIO': '05', 'Maio ': '05', 'MAIO ': '05', 'Junho': '06', 'JUNHO': '06', 'Junho ': '06', 'JUNHO ': '06', 'Julho': '07', 'JULHO': '07', 'Julho ': '07', 'JULHO ': '07', 'Agosto': '08', 'AGOSTO': '08', 'Agosto ': '08', 'AGOSTO ': '08', 'Setembro': '09', 'SETEMBRO': '09', 'Setembro ': '09', 'SETEMBRO ': '09', 'Outubro': '10', 'OUTUBRO': '10', 'Outubro ': '10', 'OUTUBRO ': '10', 'Novembro': '11', 'NOVEMBRO': '11', 'Novembro ': '11', 'NOVEMBRO ': '11', 'Dezembro': '12', 'DEZEMBRO': '12', 'Dezembro ': '12', 'DEZEMBRO ': '12', 'A DEFINIR': 'A definir', 'A DEFINIR ': 'A definir', 'A Definir': 'A definir', 'A Definir ': 'A definir'})
    
    # Tratamento da coluna 'ANO'
    data['ANO'] = data['ANO'].astype(str)
    data['ANO'] = data['ANO'].str.replace('.0', '')
    
    # Criar a coluna 'DATA' a partir de 'PREVISÃO_DE_RECEBIMENTO' e 'ANO'
    data['DATA'] = data['PREVISÃO_DE_RECEBIMENTO'] + '/' + data['ANO']
    
    # Remover colunas que não serão mais utilizadas
    data = data.drop(['PREVISÃO_DE_RECEBIMENTO', 'ANO'], axis=1)
    
    # Converter a coluna 'DATA' para o formato datetime
    data['DATA'] = pd.to_datetime(data['DATA'], format='%m/%Y', errors='coerce')
    data['DATA'] = data['DATA'].dt.strftime('%m/%Y')
    data['DATA'] = data['DATA'].fillna('A definir')
    
    # Substituir valores em branco na coluna 'CLIENTE'
    data['CLIENTE'] = data['CLIENTE'].replace({'': 'Não identificado'})
    
    # Excluir linhas com saldo a receber vazio
    data = data[data['SALDO_A_RECEBER'] != '']
    
    #Para finalizar a limpeza, utilizar agora a coluna TIPO como referência para remover linhas com valores nulos.
    data = data[data['TIPO'] != '']
    
    #EXCLUIR TODAS AS LINHAS REFERENTES A ANTES DE 01/2025 
    data = data[data['DATA'] != '01/2024']
    data = data[data['DATA'] != '02/2024']
    data = data[data['DATA'] != '03/2024']
    data = data[data['DATA'] != '04/2024']
    data = data[data['DATA'] != '05/2024']
    data = data[data['DATA'] != '06/2024']
    data = data[data['DATA'] != '07/2024']
    data = data[data['DATA'] != '08/2024']
    data = data[data['DATA'] != '09/2024']
    data = data[data['DATA'] != '10/2024']
    data = data[data['DATA'] != '11/2024']
    data = data[data['DATA'] != '12/2024']
    data = data[data['DATA'] != '01/2023']
    data = data[data['DATA'] != '02/2023']
    data = data[data['DATA'] != '03/2023']
    data = data[data['DATA'] != '04/2023']
    data = data[data['DATA'] != '05/2023']
    data = data[data['DATA'] != '06/2023']
    data = data[data['DATA'] != '07/2023']
    data = data[data['DATA'] != '08/2023']
    data = data[data['DATA'] != '09/2023']
    data = data[data['DATA'] != '10/2023']
    data = data[data['DATA'] != '11/2023']
    data = data[data['DATA'] != '12/2023']
    data = data[data['DATA'] != '01/2025']
    
    #PROJETO e PROJETO/Empresa Privada sâo a mesma coisa, vamos juntar esses dois tipos em um só
    
    data['TIPO'] = data['TIPO'].replace({'PROJETO/Empresa Privada': 'PROJETO'})


    #PROGRAMAR PARA SEMPRE REMOVER O MÊS ANTERIOR AO ATUAL

    def remove_previous_month(dataframe):
        """Remove do DataFrame as linhas que correspondem exatamente ao mês anterior ao atual (mm/YYYY)."""
        # Data de hoje
        today = datetime.date.today()
        # Primeiro dia do mês atual
        first_day_this_month = datetime.date(today.year, today.month, 1)
        # Último dia do mês anterior
        last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
        # Formatar no padrão mm/YYYY
        prev_month_str = last_day_prev_month.strftime('%m/%Y')
        
        # Remover as linhas que tenham DATA igual a prev_month_str
        filtered_df = dataframe[dataframe['DATA'] != prev_month_str]
        return filtered_df


    # Após você criar data['DATA'] e antes de plotar gráficos
    data = remove_previous_month(data)

    
    
    
    #Acima dos filtros, adicionar logo da empresa na sidebar, PNG
    #Para isso, é preciso fazer o upload da imagem para o Streamlit


    #Baixar to Bucket do S3
    logo = s3.Bucket('jsoninnovatis').Object('Logo.png').get()
    
    # Ler o conteúdo e carregar a imagem
    logo_data = logo['Body'].read()
    image = Image.open(BytesIO(logo_data))

    # Carregar a imagem
    st.sidebar.image(image, use_container_width=True)
    
    # Adicionar um CSS para aumentar em 30% o tamanho da fonte de todos os textos do filtro na sidebar
    st.markdown("""
        <style>
                
            /* Aumentar o tamanho da fonte dos filtros na sidebar */
            [data-testid="stSidebar"] * {
                font-size: 101% !important;
            }

            	.st-fx {
                background-color: rgb(49, 170, 77);  
            }

	    	.st-cx {
                border-bottom-color: rgb(49, 170, 77);  
            }

    		.st-cw {
                border-top-color: rgb(49, 170, 77);  
            }

    		.st-cv {
                border-right-color: rgb(49, 170, 77);  
           }

		.st-cu {
                border-left-color: rgb(49, 170, 77);  
           }

		.st-ei {
                background-color: #28a74500 !important;  
            }

		.st-e2 {
   		background: linear-gradient(to right, rgba(151, 166, 195, 0.25) 0%, rgba(151, 166, 195, 0.25) 0%, rgb(49 170 77 / 0%) 0%, rgb(49 170 77 / 0%) 100%, rgba(151, 166, 195, 0.25) 100%, rgba(151, 166, 195, 0.25) 100%);
	    }

		.st-e3 {
                background: linear-gradient(to right, rgba(151, 166, 195, 0.25) 0%, rgba(151, 166, 195, 0.25) 0%, rgb(49, 170, 77) 0%, rgb(49, 170, 77) 100%, rgba(151, 166, 195, 0.25) 100%, rgba(151, 166, 195, 0.25) 100%);  
            }

		.st-emotion-cache-1dj3ksd {
                background-color: #28a745 !important;  
            }

		.st-emotion-cache-15fru4 {
                padding: 0.2em 0.4em;
		        overflow-wrap: break-word;
	            margin: 0px;
	            border-radius: 0.25rem;
	            background: rgb(248, 249, 251);
	            color: rgb(9, 171, 59);
	            font-family: "Source Code Pro", monospace;
	            font-size: 0.75em;  
            }

		.st-emotion-cache-1373cj4 {
  			    font-family: "Source Code Pro", monospace;
			    font-size: 14px;
			    color: rgb(49, 170, 77);
			    top: -1.6em;
			    position: absolute;
			    white-space: nowrap;
			    background-color: transparent;
			    line-height: 1.6;
			    font-weight: 400;
			    pointer-events: none;
		    }

		.st-fi {
                background-color: rgb(49, 170, 77);  
        	    }

  		.st-hy {
    		    background-color: rgb(49, 170, 77);
	  	    }

		.st-f1 {
    		    background-color: rgb(49, 170, 77);
		    }


                
            </style>
        """, unsafe_allow_html=True)
    
    
    
    #Converter Custos Incorridos e Custos Correlatos para numérico
    data['CUSTOS_INCORRIDOS'] = data['CUSTOS_INCORRIDOS'].str.strip()
    data['CUSTOS_INCORRIDOS'] = data['CUSTOS_INCORRIDOS'].str.replace('R$', '')
    data['CUSTOS_INCORRIDOS'] = data['CUSTOS_INCORRIDOS'].str.replace('.', '')
    data['CUSTOS_INCORRIDOS'] = data['CUSTOS_INCORRIDOS'].str.replace(',', '.')
    data['CUSTOS_INCORRIDOS'] = pd.to_numeric(data['CUSTOS_INCORRIDOS'], errors='coerce')

    data['CUSTOS_CORRELATOS'] = data['CUSTOS_CORRELATOS'].str.strip()
    data['CUSTOS_CORRELATOS'] = data['CUSTOS_CORRELATOS'].str.replace('R$', '')
    data['CUSTOS_CORRELATOS'] = data['CUSTOS_CORRELATOS'].str.replace('.', '')
    data['CUSTOS_CORRELATOS'] = data['CUSTOS_CORRELATOS'].str.replace(',', '.')
    data['CUSTOS_CORRELATOS'] = pd.to_numeric(data['CUSTOS_CORRELATOS'], errors='coerce')

    #Preencher valores vazios de Custos Incorridos e Custos Correlatos com 0
    data['CUSTOS_INCORRIDOS'] = data['CUSTOS_INCORRIDOS'].fillna(0)
    data['CUSTOS_CORRELATOS'] = data['CUSTOS_CORRELATOS'].fillna(0)


    
    # Filtros interativos
    st.sidebar.header('Filtros')
    meses = st.sidebar.multiselect('Meses:', data['DATA'].unique())
    tipos = st.sidebar.multiselect('Tipos de Serviço:', data['TIPO'].unique())
    fundacoes = st.sidebar.multiselect('Fundações:', data['FUNDAÇÃO'].unique())
    clientes = st.sidebar.multiselect('Clientes:', data['CLIENTE'].unique())
    
    # Converter saldo a receber para numérico para poder aplicar o filtro de max e min:
    saldo_receber_temp = data['SALDO_A_RECEBER'].copy()
    saldo_receber_temp = saldo_receber_temp.str.strip()
    saldo_receber_temp = saldo_receber_temp.str.replace('R$', '')
    saldo_receber_temp = saldo_receber_temp.str.replace('.', '')
    saldo_receber_temp = saldo_receber_temp.str.replace(',', '.')
    saldo_receber_temp = pd.to_numeric(saldo_receber_temp, errors='coerce')
    
    # Filtro de Saldo a Receber - Valor mínimo e máximo, utilizando os valores numéricos de saldo_receber_temp
    min_saldo, max_saldo = st.sidebar.slider(
        'Selecione o intervalo de valores:',
        min_value=float(saldo_receber_temp.min()),
        max_value=float(saldo_receber_temp.max()),
        value=(float(saldo_receber_temp.min()), float(saldo_receber_temp.max())),
        step=1000.0
    )
    
    # Aplicar filtros - CRIAR UMA CÓPIA DOS DADOS FILTRADOS
    filtered_data = data.copy()
    
    if meses:
        filtered_data = filtered_data[filtered_data['DATA'].isin(meses)]
    if tipos:
        filtered_data = filtered_data[filtered_data['TIPO'].isin(tipos)]
    if fundacoes:
        filtered_data = filtered_data[filtered_data['FUNDAÇÃO'].isin(fundacoes)]
    if clientes:
        filtered_data = filtered_data[filtered_data['CLIENTE'].isin(clientes)]
    
    # Aplicar o filtro de Saldo a Receber
    filtered_data['SALDO_A_RECEBER'] = saldo_receber_temp
    filtered_data = filtered_data[filtered_data['SALDO_A_RECEBER'] >= min_saldo]
    filtered_data = filtered_data[filtered_data['SALDO_A_RECEBER'] <= max_saldo]
    
    # Exibir o número de linhas no DataFrame filtrado
    st.sidebar.subheader('Resumo dos Filtros')
    st.sidebar.write('Número de linhas:', filtered_data.shape[0])
    
    # Exibir também no Resumo dos filtros o valor total a receber pela empresa com os filtros aplicados:
    total_a_receber_filtrado = filtered_data['SALDO_A_RECEBER'].sum()
    total_a_receber_filtrado_real = f'R${total_a_receber_filtrado:,.2f}'
    st.sidebar.write('Valor Total a Receber:', total_a_receber_filtrado_real)
    
    st.subheader('Valor Total a Receber pela Empresa:')
    st.write(f'<p style="font-size:40px">{total_a_receber_filtrado_real}</p>', unsafe_allow_html=True)
    
    
    # Exibir a planilha filtrada
    if st.checkbox('Mostrar planilha filtrada'):
        st.markdown("<h3 style='font-size:140%;'>Planilha de Contas a Receber - Higienizada em tempo real</h3>", unsafe_allow_html=True)
        st.write(filtered_data)
        st.markdown(f"<p style='font-size:140%;'>Tamanho da amostra: {filtered_data.shape[0]}</p>", unsafe_allow_html=True)
    
     # Criando colunas no Streamlit
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    
    
    
    
    
    
    
    
    # Definir uma paleta de cores pastéis com predominância de azul e verde para os gráficos
    colors_palette = ['#a1c9f4', '#a1f4c9', '#a1c9f4', '#a1f4c9', '#a1c9f4', '#a1f4c9', '#f4d1a1', '#f4a1d8']
    
    # Gráficos estáticos (não alteram com filtros)
    
    # Gráfico de barras horizontais - Distribuição por Cliente (usando dados originais, sem filtros)

    with row2_col1:
        st.subheader('Distribuição por Cliente')

        # Alinhar os filtros em uma linha com três colunas (cada um com largura reduzida)
        col_date, col_tipo, col_fundacao = st.columns(3)
        
        with col_date:
            datas_disponiveis = sorted(data['DATA'].unique())
            datas_selecionadas = st.multiselect(
                "Data:",
                datas_disponiveis,
                default=[], 
                key="data_cliente"
            )
        
        with col_tipo:
            tipos_disponiveis = sorted(data['TIPO'].unique())
            tipos_selecionados = st.multiselect(
                "Tipo de Serviço:",
                tipos_disponiveis,
                default=[], 
                key="tipo_cliente"
            )
        
        with col_fundacao:
            fundacoes_disponiveis = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas = st.multiselect(
                "Fundação:",
                fundacoes_disponiveis,
                default=[], 
                key="fundacao_cliente"
            )
        
        # Filtrar os dados com base nos filtros selecionados.
        # Se nenhum filtro for selecionado, utiliza todos os dados.
        dados_local = data.copy()
        if datas_selecionadas:
            dados_local = dados_local[dados_local['DATA'].isin(datas_selecionadas)]
        if tipos_selecionados:
            dados_local = dados_local[dados_local['TIPO'].isin(tipos_selecionados)]
        if fundacoes_selecionadas:
            dados_local = dados_local[dados_local['FUNDAÇÃO'].isin(fundacoes_selecionadas)]
        
        # Garantir que a coluna SALDO_A_RECEBER tenha os valores numéricos convertidos
        dados_local['SALDO_A_RECEBER'] = saldo_receber_temp

        # Agrupar por CLIENTE e somar os valores
        total_por_cliente = dados_local.groupby('CLIENTE')['SALDO_A_RECEBER'].sum().reset_index()
        total_por_cliente = total_por_cliente.sort_values(by='SALDO_A_RECEBER', ascending=False)

        # Agregar clientes com participação inferior a 3% em "Outros"
        total_por_cliente['CLIENTE_AGRUPADO'] = total_por_cliente['CLIENTE']
        total_por_cliente.loc[
            total_por_cliente['SALDO_A_RECEBER'] / total_por_cliente['SALDO_A_RECEBER'].sum() < 0.03,
            'CLIENTE_AGRUPADO'
        ] = 'Outros'

        # Agrupar os valores por CLIENTE_AGRUPADO e ordenar para exibição em barras horizontais
        agrupado = total_por_cliente.groupby('CLIENTE_AGRUPADO')['SALDO_A_RECEBER'].sum().reset_index()
        agrupado = agrupado.sort_values(by='SALDO_A_RECEBER', ascending=True)

        # Escalar os valores para milhões
        agrupado['SALDO_A_RECEBER'] /= 1_000_000

        # Selecionar as cores conforme a paleta definida
        cores = colors_palette[:len(agrupado)]

        fig_bar, ax_bar = plt.subplots(figsize=(3, 2))
        ax_bar.barh(agrupado['CLIENTE_AGRUPADO'], agrupado['SALDO_A_RECEBER'], color=cores)
        ax_bar.set_xlabel('Saldo a Receber (em milhões)', fontsize=5)
        ax_bar.set_ylabel('Cliente', fontsize=5)
        ax_bar.ticklabel_format(style='plain', axis='x', useOffset=False)
        ax_bar.tick_params(axis='x', labelsize=4)
        ax_bar.tick_params(axis='y', labelsize=4)

        # Exibir os valores ao lado das barras
        for i, v in enumerate(agrupado['SALDO_A_RECEBER']):
            ax_bar.text(v + (v * 0.01), i, f'R${v:,.2f}M', va='center', fontsize=4, color='black')

        st.pyplot(fig_bar, use_container_width=False)





    
    




    
    # Gráfico de Pizza: Distribuição dos Custos Incorridos e Custos Correlatos
    with row2_col2:
        st.subheader('Distribuição dos Custos')

        # Alinhar os filtros em uma única linha com três colunas (largura reduzida)
        col1, col2, col3 = st.columns(3)
        with col1:
            datas_disponiveis_custos = sorted(data['DATA'].unique())
            datas_selecionadas_custos = st.multiselect(
                "Data:",
                datas_disponiveis_custos,
                default=[], 
                key="data_custos"
            )
        with col2:
            fundacoes_disponiveis_custos = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas_custos = st.multiselect(
                "Fundação:",
                fundacoes_disponiveis_custos,
                default=[], 
                key="fundacao_custos"
            )
        with col3:
            clientes_disponiveis_custos = sorted(data['CLIENTE'].unique())
            clientes_selecionados_custos = st.multiselect(
                "Cliente:",
                clientes_disponiveis_custos,
                default=[], 
                key="cliente_custos"
            )

        # Filtrar os dados localmente com base nos filtros selecionados
        dados_local_custos = data.copy()
        if datas_selecionadas_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['DATA'].isin(datas_selecionadas_custos)]
        if fundacoes_selecionadas_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['FUNDAÇÃO'].isin(fundacoes_selecionadas_custos)]
        if clientes_selecionados_custos:
            dados_local_custos = dados_local_custos[dados_local_custos['CLIENTE'].isin(clientes_selecionados_custos)]

        # Calcular os totais de custos usando os dados filtrados localmente
        total_custos_incurridos = dados_local_custos['CUSTOS_INCORRIDOS'].sum()
        total_custos_correlatos = dados_local_custos['CUSTOS_CORRELATOS'].sum()

        custos_labels = ['Custos Incorridos', 'Custos Correlatos']
        custos_values = [total_custos_incurridos, total_custos_correlatos]

        color_map = {
            'Custos Incorridos': '#a1c9f4',  # azul pastel
            'Custos Correlatos': '#a1f4c9'     # verde pastel
        }
        custos_colors = [color_map[label] for label in custos_labels]

        # Função para formatar a exibição de cada fatia (percentual e valor)
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

        # Criar uma linha para os filtros (Data e Tipo de Serviço) com colunas menores
        col_date, col_tipo = st.columns(2)
        
        with col_date:
            datas_disponiveis_fundacao = sorted(data['DATA'].unique())
            datas_selecionadas_fundacao = st.multiselect(
                "Data:",
                datas_disponiveis_fundacao,
                default=[], 
                key="data_fundacao"
            )
        
        with col_tipo:
            tipos_disponiveis = sorted(data['TIPO'].unique())
            tipos_selecionados = st.multiselect(
                "Tipo de Serviço:",
                tipos_disponiveis,
                default=[], 
                key="tipo_fundacao"
            )
        
        # Filtrar os dados com base no(s) filtro(s)
        dados_local_fundacao = data.copy()
        if datas_selecionadas_fundacao:
            dados_local_fundacao = dados_local_fundacao[dados_local_fundacao['DATA'].isin(datas_selecionadas_fundacao)]
        if tipos_selecionados:
            dados_local_fundacao = dados_local_fundacao[dados_local_fundacao['TIPO'].isin(tipos_selecionados)]
        
        # Garantir que a coluna SALDO_A_RECEBER contenha valores numéricos
        dados_local_fundacao['SALDO_A_RECEBER'] = saldo_receber_temp

        # Agrupar os dados por FUNDAÇÃO e somar os valores
        total_a_receber_por_fundacao = dados_local_fundacao.groupby('FUNDAÇÃO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_fundacao['SALDO_A_RECEBER'] = pd.to_numeric(total_a_receber_por_fundacao['SALDO_A_RECEBER'], errors='coerce')
        total_a_receber_por_fundacao = total_a_receber_por_fundacao.sort_values(by='SALDO_A_RECEBER', ascending=False)

        fig_bar_fundacao, ax_bar_fundacao = plt.subplots(figsize=(3, 2))
        # Utilizar a cor verde predominante da paleta para as barras
        ax_bar_fundacao.bar(
            total_a_receber_por_fundacao['FUNDAÇÃO'],
            total_a_receber_por_fundacao['SALDO_A_RECEBER'],
            color=colors_palette[1]
        )
        ax_bar_fundacao.set_ylabel('Valor total a receber', fontsize=5)
        ax_bar_fundacao.set_xlabel('Fundação', fontsize=5)

        # Converter cada valor para float antes de somar e exibir
        for i, v in enumerate(total_a_receber_por_fundacao['SALDO_A_RECEBER']):
            num_val = float(v)
            ax_bar_fundacao.text(
                i, 
                num_val + 10000, 
                f'R${num_val:,.0f}', 
                ha='center', 
                va='bottom', 
                fontsize=5
            )

        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_fundacao, use_container_width=False)











    # Gráfico de barras - Distribuição de Valor a Receber por Tipo de Serviço
    with row1_col2:
        st.subheader('Valor a Receber por Tipo de Serviço')
        
        # Alinhar os filtros em uma linha com duas colunas (Data e Fundação)
        col_date, col_fundacao = st.columns(2)
        
        with col_date:
            datas_disponiveis_tipo = sorted(data['DATA'].unique())
            datas_selecionadas_tipo = st.multiselect(
                "Data:",
                datas_disponiveis_tipo,
                default=[], 
                key="data_tipo"
            )
        
        with col_fundacao:
            fundacoes_disponiveis_tipo = sorted(data['FUNDAÇÃO'].unique())
            fundacoes_selecionadas_tipo = st.multiselect(
                "Fundação:",
                fundacoes_disponiveis_tipo,
                default=[], 
                key="fundacao_tipo"
            )
        
        # Filtrar os dados com base nos filtros selecionados
        dados_local_tipo = data.copy()
        if datas_selecionadas_tipo:
            dados_local_tipo = dados_local_tipo[dados_local_tipo['DATA'].isin(datas_selecionadas_tipo)]
        if fundacoes_selecionadas_tipo:
            dados_local_tipo = dados_local_tipo[dados_local_tipo['FUNDAÇÃO'].isin(fundacoes_selecionadas_tipo)]
        
        # Não filtramos por TIPO, para incluir todos os tipos no agrupamento.
        # Atualizar a coluna SALDO_A_RECEBER com os valores numéricos convertidos.
        dados_local_tipo['SALDO_A_RECEBER'] = saldo_receber_temp
        
        # Agrupar os dados por TIPO e somar os valores
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
        
        # Exibir os valores ao lado das barras
        for i, v in enumerate(total_a_receber_por_tipo['SALDO_A_RECEBER']):
            num_val = float(v)
            ax_bar_tipo.text(
                i, 
                num_val + 10000, 
                f'R${num_val:,.0f}', 
                ha='center', 
                va='bottom', 
                fontsize=5
            )
        
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_tipo, use_container_width=False)
