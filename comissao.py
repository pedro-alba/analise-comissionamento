import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
#Diminuir tamanho do cabeçalho do streamlit
st.write('<style>div.block-container{padding-top:1rem; }</style>', unsafe_allow_html=True)
#Design dos elementos
st.markdown(
"""
    <style>
    .stApp {
        background: linear-gradient(45deg, #191e26, #2d3645);  /* Gradient from pink to orange */
        color: #ffffff;
    }
    .stAppHeader {
        background: linear-gradient(45deg, #191e26, #2d3645);  /* Same gradient for the header */
        color: #ffffff;  /* White text for better contrast */
    }
    .block-container {
        padding: 2rem;  /* Adjust padding around the whole Streamlit content */
    }
    [data-testid="stSidebarContent"] {
        color: white;
        background-color: #20252e;
    }
    .stPlotlyChart {
            box-shadow: 10px 10px 20px 4px rgba(0, 0, 0, 0.25);  /* Apply shadow */
            padding: 10px;
            border-radius: 8px;  /* Optional: rounded corners */
            color: white;
            background-color: #20252e;
            margin: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

def clean_df(uploaded_file):
    #Importar dataframe
    colunas = [
        'Data e hora', 'Venda', 'Status da venda', 'Funcionário', 'Tipo do Item',
        'Grupo', 'Produto/serviço', 'Quantidade', 'Líquido']
    df = pd.read_csv(uploaded_file, sep=';', usecols= colunas)

    #Filtrar por vendas baixadas, por produtos e pelos grupos específicos
    df = df[df['Status da venda'] == 'Baixado']
    df = df[df['Tipo do Item'] == 'Produto']
    grupos_desejados = ['Farmácia', 'Biscoitos e Petiscos', 'Antiparasitários', 'Acessórios', 'Roupa', 'Ração úmida']
    df = df[df['Grupo'].isin(grupos_desejados)]

    #Coluna 'Líquido' para float, tratamento de strings
    df['Líquido'] = df['Líquido'].str.replace(',','.')
    df['Líquido'] = df['Líquido'].apply(lambda x: float(x))
    df['Funcionário'] = df['Funcionário'].str.lower()
    df['Produto/serviço'] = df['Produto/serviço'].str.lower()

    #Conversão de data e hora
    df['data'] = df['Data e hora'].str.split(' ').str[0]
    del df['Data e hora']
    df.set_index('data')
    df['data'] = pd.to_datetime(df['data'], format="%d/%m/%Y")
    df['mes'] = pd.to_datetime(df['data']).dt.month
    df['ano'] = pd.to_datetime(df['data']).dt.year
    ano = st.sidebar.selectbox("Ano", df['ano'].unique())

    #Quantidade para int
    df['Quantidade'] = df['Quantidade'].str.replace(',', '.')
    df['Quantidade'] = df['Quantidade'].astype(float).astype(int)
    
    return operacoes(df)

def operacoes(df):
    #Total mensal
    total_mes = df.groupby('mes')['Líquido'].sum().rename('faturamento').reset_index()
    #Faturamento médio e total
    faturamento_medio = np.round(df.groupby('mes')['Líquido'].sum().mean(), 2)
    faturamento_total = np.round(df.groupby('mes')['Líquido'].sum(), 2)
    #Soma por quantidade, excluindo produtos vendidos por comprimido
    df_sem_comp = df[~df['Produto/serviço'].str.contains('comp', case=False, na=False)]
    qtd_produto = df_sem_comp.groupby('Produto/serviço')['Quantidade'].sum().sort_values(ascending=False).head(20).rename('quantidade').reset_index()
    #Lucro em R$ por produto
    lucro_produto = df.groupby('Produto/serviço')['Líquido'].sum().sort_values(ascending=False).head(20).rename('lucro').reset_index()
    #Vendas por funcionário
    venda_funcionario = df.groupby('Funcionário')['Líquido'].sum().sort_values(ascending=False).rename('lucro').reset_index()
    venda_funcionario['Funcionário'] = venda_funcionario['Funcionário'].apply(lambda x: f"{x.split()[0]} {x.split()[1][0]}." if len(x.split()) > 1 else x)
    
    #Unindo todas as categorias de Bravecto e Milbemax em uma
    bravecto_milbemax = df
    bravecto_milbemax['Produto/serviço'] = df['Produto/serviço'].apply(
        lambda x: 'bravecto' if 'bravecto' in x.lower() else ('milbemax' if 'milbemax' in x.lower() else x)
    )
    #Filtrando apenas Bravecto e Milbemax
    bravecto_milbemax = bravecto_milbemax[bravecto_milbemax['Produto/serviço'].isin(['bravecto', 'milbemax'])]
    #Agrupando e somando por mês para criação do gráfico de linhas
    bravecto_milbemax = bravecto_milbemax.groupby(['Produto/serviço', 'mes'])['Líquido'].sum().reset_index()

    return gerar_graficos(total_mes, qtd_produto, lucro_produto, venda_funcionario, bravecto_milbemax)

def gerar_graficos(total_mes, qtd_produto, lucro_produto, venda_funcionario, bravecto_milbemax):
    def estilizar_grafico(fig, title_x=0.5, title_y=0.95):
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            title_x=title_x,
            title_y=title_y,
            title_font=dict(size=18, family="Arial, sans-serif", color='#ffffff'),
            font=dict(family="Arial, sans-serif", size=14, color="rgb(255, 255, 255)"),
            xaxis=dict(showgrid=False, fixedrange=True, title=None),
            yaxis=dict(showgrid=False, fixedrange=True, rangemode='tozero', title=None),
            margin=dict(t=40, b=40, l=60, r=60),
            #showlegend=False
        )
        return fig

    # Gráfico 1: Faturamento mensal
    fig_faturamento = px.line(total_mes, x='mes', y='faturamento', title='Faturamento mensal', markers=True)
    estilizar_grafico(fig_faturamento)
    st.plotly_chart(fig_faturamento, use_container_width=True)

    # Configurar colunas
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # Gráfico 2: Quantidade de produtos
    fig_qtd = px.bar(qtd_produto, x='quantidade', y='Produto/serviço', orientation='h', title="Produtos - Quantidade")
    estilizar_grafico(fig_qtd, title_x=0.6)
    with col2:
        st.plotly_chart(fig_qtd, use_container_width=True)

    # Gráfico 3: Lucro de produtos
    fig_lucro = px.bar(lucro_produto, x='lucro', y='Produto/serviço', orientation='h', title="Produtos - Faturamento")
    estilizar_grafico(fig_lucro, title_x=0.6)
    with col1:
        st.plotly_chart(fig_lucro, use_container_width=True)

    # Gráfico 4: Vendas por funcionário
    fig_venda_func = px.bar(venda_funcionario.head(10), x='Funcionário', y='lucro', orientation='v', title="Vendas por funcionário")
    estilizar_grafico(fig_venda_func, title_x=0.6)
    with col3:
        st.plotly_chart(fig_venda_func, use_container_width=True)

    # Gráfico 5: Bravecto e Milbemax
    fig_bravecto = px.line(
        bravecto_milbemax, 
        x='mes', 
        y='Líquido', 
        color='Produto/serviço', 
        title='Venda mensal de Bravecto e Milbemax', 
        markers=True
    )
    estilizar_grafico(fig_bravecto, title_x=0.4)
    fig_bravecto.update_layout(
        legend=dict(
            font=dict(
                family="Arial, sans-serif",  # Font family for the legend
                size=14,  # Font size for the legend
                color="rgb(255, 255, 255)"  # Set the legend font color explicitly
            ),
            title=None,  # Remove legend title (if any)
            y=0.05,  # Move the legend lower (0 = bottom, 1 = top)
            x=0.1,  # Center the legend horizontally
            xanchor="center",  # Anchor the legend horizontally at its center
            yanchor="bottom"  # Anchor the legend vertically at its bottom
        ),
    )
    with col4:
        st.plotly_chart(fig_bravecto, use_container_width=True, key="bravecto_milbemax_chart")



#Título
st.title("Análise de comissionamento")
st.markdown("---")

#Upload de arquivo
uploaded_file = st.file_uploader("Envie o arquivo de vendas", type=["csv"])

if uploaded_file:
    
    clean_df(uploaded_file)

else:
    st.write("Por favor, envie um arquivo para análise.")