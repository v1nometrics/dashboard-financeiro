# Dashboard Financeiro (v1.5)

Um dashboard financeiro abrangente desenvolvido em Streamlit para monitoramento e análise de projetos financeiros vinculados a fundações, com capacidades avançadas de rastreamento de receitas, análise de desvios e gestão de repasses.

## 📋 Visão Geral

Este sistema oferece uma plataforma completa para:
- Monitoramento de valores a receber por projeto
- Identificação de repasses em atraso
- Análise de desvios de proporção financeira
- Visualização interativa de dados financeiros
- Exportação de relatórios formatados para Excel

## ✨ Funcionalidades Principais

### 🔐 Sistema de Autenticação
- Login seguro de usuários
- Controle de acesso baseado em credenciais
- Sessão persistente com cookies

### 📊 Monitoramento Financeiro
- **Planilha de Contas a Receber**: Visualização detalhada de valores pendentes
- **Repasses em Atraso**: Identificação automática de parcelas atrasadas
- **Desvio de Proporção**: Análise de discrepâncias entre repasses e custos
- **Filtros Avançados**: Por mês, tipo de serviço, fundação, cliente e faixa de valores

### 📈 Análise Gráfica Interativa
- Distribuição de valores por cliente
- Análise por fundação
- Segmentação por tipo de serviço
- Distribuição de custos (incorridos vs correlatos)
- Insights automáticos gerados em tempo real

### 📥 Exportação e Relatórios
- Exportação para Excel com formatação avançada
- Colorização automática por projeto
- Formatação de moeda brasileira
- Relatórios personalizados baseados em filtros

### 🔄 Integração de Dados
- Sincronização automática com Google Sheets
- Processamento de células mescladas
- Tratamento inteligente de dados duplicados
- Cálculos proporcionais baseados em filtros

## 🔬 Peculiaridades Técnicas Avançadas

### 🎨 Sistema de Cores Inteligente
- **Geração Automática**: Algoritmo baseado em HSV color space com Golden Ratio
- **Paletas Padronizadas**: 6 famílias de cores (blues, greens, yellows, pinks, grays, oranges)
- **Conversão Dinâmica**: RGBA para HEX para compatibilidade Excel
- **Mapeamento Consistente**: Cores mantidas entre tabelas e gráficos
- **Identificação Visual**: Projetos agrupados visualmente por cor única

### 🧮 Algoritmos de Cálculo Avançados
- **Desvio por Tolerância**: Sistema com tolerância de R$ 20,00 para análise de proporção
- **Correção de Grupo**: Análise por bloco de projeto vs linha individual
- **Cálculo Proporcional**: "SALDO A RECEBER PREVISTO ATÉ A DATA FILTRADA" baseado em proporção de custos
- **Tratamento "A Definir"**: Lógica específica para datas indefinidas
- **Agregação Inteligente**: Evita duplicação de saldos por projeto

### 📊 Processamento Excel Sofisticado
- **Células Mescladas**: Tratamento automático com OpenPyXL antes do processamento
- **Formatação Condicional**: Moeda brasileira, percentuais e números
- **Ajuste Automático**: Largura de colunas baseada no conteúdo
- **Colorização por Projeto**: Linhas coloridas automaticamente por ID do projeto
- **Validação de Dados**: Conversão robusta de tipos de dados

### 🤖 Análise Automática com IA
- **Insights em Tempo Real**: Análise automática de cada gráfico
- **Detecção de Padrões**: Concentração, diversificação e tendências
- **Métricas Dinâmicas**: Percentuais e comparações calculados automaticamente
- **Recomendações**: Insights específicos por tipo de visualização

### ⚡ Otimizações de Performance
- **Cache Inteligente (v1.5)**: uso extensivo de `@st.cache_data` (pré-processamento do Excel, geração de planilhas, mapas de cores e consultas do histórico) para tornar trocas de seleção instantâneas.
- **Botão “Forçar atualização de dados” (v1.5)**: limpa todo o cache do aplicativo e recarrega as fontes do zero; útil quando a base de dados externa foi atualizada.
- **Controle de Rerun**: Prevenção de recarregamentos desnecessários
- **Session State**: Persistência de filtros e estados de interface
- **Processamento Assíncrono**: Carregamento otimizado de dados

### 🔗 Integrações Específicas
- **Google Drive API**: Exportação direta de XLSX do Google Sheets
- **AWS S3**: Armazenamento seguro de credenciais JSON
- **Processamento Seletivo**: Exclusão automática de abas específicas
- **Múltiplas Fontes**: Consolidação de dados de diferentes planilhas

### 🔢 Identificação e Agregação de Projetos
- **Chave Única**: Combinação `PÁGINA_QUANT.` garante identificação correta de projetos
- **Prevenção de Duplicidade**: Cada projeto é contabilizado uma única vez em seu valor total
- **Integridade por Origem**: Reconhecimento que projetos são únicos por aba de origem
- **Agregação Correta**: Totalização precisa do valor global a receber (~R$ 14 milhões)
- **Tratamento de Linhas**: Manipulação inteligente de linhas repetidas do mesmo projeto

## 🛠️ Tecnologias Utilizadas

### Backend e Processamento
- **Python**: Linguagem principal
- **Pandas**: Manipulação e análise de dados
- **NumPy**: Operações numéricas
- **OpenPyXL**: Processamento avançado de Excel

### Interface e Visualização
- **Streamlit**: Framework web para dashboards
- **Matplotlib**: Criação de gráficos
- **Streamlit Authenticator**: Sistema de autenticação

### Integração e APIs
- **Boto3**: Acesso ao AWS S3
- **Gspread**: API do Google Sheets
- **OAuth2Client**: Autorização de tokens Google
- **Google API Client**: Integração com Google Drive

### Processamento de Dados
- **JSON**: Manipulação de dados estruturados
- **YAML**: Configurações do sistema
- **Datetime**: Manipulação de data e hora
- **Pillow (PIL)**: Processamento de imagens
- **io.BytesIO**: Manipulação de arquivos em memória
- **Re (Regex)**: Processamento de texto avançado

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- Conta AWS S3
- Acesso ao Google Sheets API
- Credenciais de serviço Google

### Dependências
```bash
pip install streamlit pandas numpy openpyxl matplotlib streamlit-authenticator boto3 gspread oauth2client google-api-python-client pillow pyyaml
```

### Configuração
1. **Arquivo de Configuração**: Configure `config.yaml` com credenciais de usuários
2. **AWS S3**: Configure acesso ao bucket com chaves de API
3. **Google Sheets**: Configure credenciais de serviço no S3
4. **Variáveis de Ambiente**: Configure chaves de acesso necessárias

## 🚀 Como Usar

### Inicialização
```bash
streamlit run app.py
```

### Fluxo de Trabalho
1. **Login**: Acesse com suas credenciais
2. **Aplicar Filtros**: Use a barra lateral para filtrar dados
3. **Visualizar Dados**: Explore as diferentes seções do dashboard
4. **Analisar Desvios**: Monitore alertas de atraso e proporção
5. **Exportar Relatórios**: Baixe planilhas formatadas conforme necessário

## 📊 Estrutura de Dados

### Campos Principais
- **Projeto**: Informações do projeto e cliente
- **Valores**: Contratos, repasses e saldos
- **Datas**: Previsões e recebimentos
- **Custos**: Incorridos e correlatos
- **Status**: Situação de pagamentos

### Cálculos Automáticos
- Proporções de repasse por projeto
- Valores esperados vs realizados
- Desvios monetários e percentuais
- Projeções baseadas em filtros temporais

## 🎯 Principais Métricas

### Dashboard Principal
- Valor total a receber pela empresa
- Distribuição por fundação/cliente
- Análise temporal de recebimentos

### Alertas de Atraso
- Projetos com repasses em atraso
- Valores atrasados por projeto
- Tempo médio de atraso

### Análise de Desvios
- Taxa de conformidade financeira
- Desvios totais e médios
- Projetos com discrepâncias

## 🔧 Personalização

### Cores e Temas
- Paleta de cores padronizada
- Colorização automática por projeto
- Tema corporativo Innovatis

### Filtros Customizáveis
- Intervalos de datas flexíveis
- Múltiplas dimensões de filtro
- Persistência de preferências

## 📝 Notas Técnicas

### Performance
- Cache de dados para otimização
- Processamento assíncrono
- Gerenciamento eficiente de memória

### Segurança
- Autenticação robusta
- Chaves seguras no S3
- Validação de dados de entrada

## 🛠️ Atualizações Recentes

### Novidades v1.5
- **Botão “Forçar atualização de dados”**: adiciona um atalho visual para apagar o cache (`st.cache_data.clear()`) e recarregar tudo automaticamente.
- **Histórico de Faturamento**: carregamento cacheado, seleção de ano/mês instantânea, e novos botões para baixar o histórico completo em Excel e para exibição da tabela completa no app.
- **Consistência Visual**: dropdowns do “Histórico de Faturamento” com o mesmo estilo (cores, bordas, hover) de “Repasses em Atraso”.

### Correções no Cálculo do Valor Total a Receber
- **Identificação Única de Projetos**: Implementação de chave composta `PÁGINA_QUANT.` para garantir a correta contabilização
- **Integridade por Aba**: Reconhecimento que cada aba contém projetos únicos, mesmo com números de `QUANT.` repetidos
- **Correção de Agregação**: Ajuste para correta totalização dos valores (~R$ 14 milhões)
- **Prevenção de Duplicidade**: Tratamento adequado de linhas repetidas do mesmo projeto
- **Otimização de Código**: Simplificação de chave de projeto para maior performance e confiabilidade

### Melhorias nos Filtros e Análise Gráfica (v1.5)
- **Lógica de Atrasos Corrigida**: A verificação de "Repasses em Atraso" agora compara as datas de forma precisa, garantindo que apenas registros genuinamente anteriores ao mês atual sejam considerados.
- **Filtro de Meses Otimizado**: O filtro "Meses (Previsão)" foi aprimorado para:
  - Exibir a opção "A definir" no topo da lista para melhor usabilidade.
  - Mostrar apenas datas a partir do mês atual, limpando a visualização.
- **Consistência nos Filtros dos Gráficos**: Os filtros da seção "Análise Gráfica" foram alinhados com o filtro principal, usando uma fonte de dados unificada e completa (`df_desvio`) para garantir que todas as opções de data relevantes sejam exibidas.
- **Correção nos Cálculos dos Gráficos**: A lógica de cálculo dos gráficos foi ajustada para usar o DataFrame completo e agregar os dados corretamente, resolvendo o problema de gráficos em branco e erros (`out-of-bounds`) ao aplicar filtros de data.
- **Análise Automática Robusta**: A geração de insights automáticos agora é mais segura e não causa erros quando os filtros resultam em um conjunto de dados vazio.

## 🤝 Contribuição

Este projeto foi desenvolvido para atender necessidades específicas de gestão financeira de projetos vinculados a fundações. Para contribuições ou melhorias, entre em contato com a equipe de desenvolvimento.

## 📄 Licença

Dashboard Financeiro Versão 1.5 © 2025 - Innovatis
