import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import json
import gdown
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import boto3
import json
from io import BytesIO
from PIL import Image

#Carregar flat logo via URL direta
logo_flat = 'https://www.innovatismc.com.br/wp-content/uploads/2023/12/logo-innovatis-flatico-150x150.png'
st.set_page_config(layout="wide", page_title='INNOVATIS DB FIN', page_icon=logo_flat)



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
st.title('Dashboard Financeiro - INNOVATIS')

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
elif st.session_state["authentication_status"] is None:
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
    data = df[['FUNDAÇÃO', 'CLIENTE', 'TIPO', 'PREVISÃO_DE_RECEBIMENTO', 'ANO', 'SALDO_A_RECEBER']]
    
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
	
		.st-d5 {
   		    background: linear-gradient(to right, rgba(151, 166, 195, 0.25) 0%, rgba(151, 166, 195, 0.25) 0%, rgb(49, 170, 77) 0%, rgb(49, 170, 77) 100%, rgba(151, 166, 195, 0.25) 100%, rgba(151, 166, 195, 0.25) 100%);
		    }


                
            </style>
        """, unsafe_allow_html=True)
    
    
    
    
    
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
        'Selecione o intervalo de Saldo a Receber:',
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
    
    # Gráfico de pizza - Distribuição por Cliente (usando dados originais, sem filtros)
    with row1_col1:
        st.subheader('Distribuição por Cliente')
        # Calcular o valor total a receber pela empresa por cliente
        data['SALDO_A_RECEBER'] = saldo_receber_temp
        total_a_receber_por_cliente = data.groupby('CLIENTE')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_cliente = total_a_receber_por_cliente.sort_values(by='SALDO_A_RECEBER', ascending=False)
    
        # Agregar clientes que representam menos de 3% cada em um grupo chamado 'Outros'
        total_a_receber_por_cliente['CLIENTE_AGRUPADO'] = total_a_receber_por_cliente['CLIENTE']
        total_a_receber_por_cliente.loc[
            total_a_receber_por_cliente['SALDO_A_RECEBER'] / total_a_receber_por_cliente['SALDO_A_RECEBER'].sum() < 0.03,
            'CLIENTE_AGRUPADO'
        ] = 'Outros'
    
        # Calcular o valor total a receber por cliente agrupado
        total_a_receber_por_cliente_agrupado = total_a_receber_por_cliente.groupby('CLIENTE_AGRUPADO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_cliente_agrupado = total_a_receber_por_cliente_agrupado.sort_values(by='SALDO_A_RECEBER', ascending=False)
    
        # Selecionar cores para o gráfico de pizza usando a nova paleta
        cores_cliente = colors_palette[:len(total_a_receber_por_cliente_agrupado)]
    
        fig_pizza, ax_pizza = plt.subplots(figsize=(2, 2))
        ax_pizza.pie(
            total_a_receber_por_cliente_agrupado['SALDO_A_RECEBER'],
            labels=total_a_receber_por_cliente_agrupado['CLIENTE_AGRUPADO'],
            autopct='%1.1f%%',
            startangle=60,
            colors=cores_cliente
        )
        ax_pizza.axis('equal')  # Equaliza o aspecto para que o gráfico seja um círculo
        st.pyplot(fig_pizza, use_container_width=False)
    
    
    
    # Gráfico de barras - Distribuição de Valor a Receber por Fundação
    with row2_col1:
        st.subheader('Valor a Receber por Fundação')
        total_a_receber_por_fundacao = data.groupby('FUNDAÇÃO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_fundacao = total_a_receber_por_fundacao.sort_values(by='SALDO_A_RECEBER', ascending=False)
    
        fig_bar_fundacao, ax_bar_fundacao = plt.subplots(figsize=(3, 2))
        # Utilizar a cor verde predominante da paleta para as barras
        ax_bar_fundacao.bar(total_a_receber_por_fundacao['FUNDAÇÃO'], total_a_receber_por_fundacao['SALDO_A_RECEBER'], color=colors_palette[1])
        ax_bar_fundacao.set_ylabel('Valor total a receber (Em milhôes)', fontsize=5)
        ax_bar_fundacao.set_xlabel('Fundação', fontsize=5)
    
        for i, v in enumerate(total_a_receber_por_fundacao['SALDO_A_RECEBER']):
            ax_bar_fundacao.text(i, v + 10000, f'R${v:,.0f}', ha='center', va='bottom', fontsize=5)
    
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar_fundacao, use_container_width=False)
    
    # Gráfico de Pizza: Distribuição do Valor a Receber por Semestre
    with row1_col2:
        # Converter a coluna DATA para datetime e criar a coluna SEMESTRE robustamente
        data['DATA_DT'] = pd.to_datetime(data['DATA'], format='%m/%Y', errors='coerce')
        data['SEMESTRE'] = data['DATA_DT'].apply(
            lambda x: f"{x.year}.{((x.month - 1) // 6) + 1}" if pd.notnull(x) else 'A definir'
        )
    
        total_a_receber_por_semestre = data.groupby('SEMESTRE')['SALDO_A_RECEBER'].sum().reset_index()
    
        # Mapeamento de cores com predominância de azul e verde para semestres
        color_map = {
            '2025.1': '#a1c9f4',  # azul pastel
            '2025.2': '#a1f4c9',  # verde pastel
            '2026.1': '#aec7e8',  # azul claro
            '2026.2': '#98df8a',  # verde claro
            '2027.1': '#a1c9f4',  # reutilizando azul
            'A definir': '#D3D3D3'  # cinza claro para indefinido
        }
    
        labels = total_a_receber_por_semestre['SEMESTRE'].apply(
            lambda x: 'A definir (sem data)' if x == 'A definir' else x
        )
        colors_semestre = [color_map.get(x, '#d3d3d3') for x in total_a_receber_por_semestre['SEMESTRE']]
    
        fig_pizza, ax_pizza = plt.subplots(figsize=(2, 2))
        wedges, texts, autotexts = ax_pizza.pie(
            total_a_receber_por_semestre['SALDO_A_RECEBER'],
            labels=labels,
            autopct='%1.1f%%',
            startangle=60,
            colors=colors_semestre,
            textprops={'fontsize': 5}
        )
        # Posicionar a legenda fora do gráfico para evitar sobreposição
        plt.legend(labels, fontsize=5, loc='center left', bbox_to_anchor=(1, 0.5))
        ax_pizza.axis('equal')
    
        st.subheader('Distribuição do Valor a Receber por Semestre')
        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        st.pyplot(fig_pizza, use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)
        
    
    # Gráfico de barras - Distribuição de Valor a Receber por Tipo de Serviço
    with row2_col2:
        st.subheader('Valor a Receber por Tipo de Serviço')
        total_a_receber_por_tipo = data.groupby('TIPO')['SALDO_A_RECEBER'].sum().reset_index()
        total_a_receber_por_tipo = total_a_receber_por_tipo.sort_values(by='SALDO_A_RECEBER', ascending=False)
    
        fig_bar, ax_bar = plt.subplots(figsize=(3, 2))
        # Utilizar a cor azul predominante da paleta para as barras
        ax_bar.bar(total_a_receber_por_tipo['TIPO'], total_a_receber_por_tipo['SALDO_A_RECEBER'], color=colors_palette[0])
        ax_bar.set_ylabel('Valor total a receber (Em milhôes)', fontsize=5)
        ax_bar.set_xlabel('Tipo de Serviço', fontsize=5)
    
        # Exibir as anotações de valores formatados nas barras
        for i, v in enumerate(total_a_receber_por_tipo['SALDO_A_RECEBER']):
            ax_bar.text(i, v + 10000, f'R${v:,.0f}', ha='center', va='bottom', fontsize=5)
    
        plt.ticklabel_format(axis='y', style='plain')
        plt.xticks(rotation=0, ha='center', fontsize=5)
        plt.yticks(fontsize=5)
        plt.tight_layout()
        st.pyplot(fig_bar, use_container_width=False)




