import pandas as pd
import re
import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from helpers import imprimir_familia_extensa, ids_lista

# Configurações globais
ALTURA_DATAFRAME = 360
CORES_GRAFO = {"Ambos": "blue", "Somente ID1": "green", "Somente ID2": "red", "Nenhum": "gray"}
CSS_ESTILO = """
<style>
    .block-container { padding-top: 1.3rem; padding-bottom: 1rem; }
    .centered-title { text-align: center; font-size: 32px; font-weight: bold; margin-bottom: 5px; color: #DAEAB5; } 
    .custom-subheader {
        font-size: 16px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
        color: #DAEAB5;
    }        
    .info-quant {
        font-size: 14px;
        text-align: center;
        margin-top: 5px;
        color: #DAEAB5;
    }
        .info-text {
        font-size: 14px;
        text-align: center;
        margin-top: 5px;
        color: #D9D3CC;
    }
</style>
"""

# Funções auxiliares
def buscar_nomes_por_ids(df, ids):
    """Busca os nomes associados a uma lista de IDs em um DataFrame."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["ID", "Nome Completo"])
    
    if "ID" in df.columns:  # Caso a coluna "ID" exista
        df_filtrado = df[df["ID"].isin(ids)][["ID", "Nome Completo"]]
    else:  # Caso os IDs estejam no índice
        df_filtrado = df.loc[df.index.intersection(ids), ["Nome Completo"]].reset_index().rename(columns={"index": "ID"})
    
    return df_filtrado.sort_values(by="ID")

def processar_id(familia_df, id_selecionado):
    """Processa um ID, extrai IDs relacionados com base na estrutura."""
    from io import StringIO
    import sys

    buffer = StringIO()
    sys.stdout = buffer
    imprimir_familia_extensa(familia_df, id_selecionado)
    sys.stdout = sys.__stdout__
    resultado = buffer.getvalue()
    buffer.close()

    ids_encontrados = []
    for linha in resultado.strip().split("\n"):
        match = re.search(r"ID:\s*(\d+)", linha)
        if match:
            ids_encontrados.append(int(match.group(1)))

    return sorted(set(ids_encontrados))

def criar_grafo_com_nomes(tabelas):
    """Cria um grafo com os nomes associados aos grupos."""
    grafo = nx.Graph()

    def adicionar_nos_e_arestas(grafo, tabela, grupo):
        for _, row in tabela.iterrows():
            grafo.add_node(row["Nome Completo"], group=grupo)
            grafo.add_edge(grupo, row["Nome Completo"])

    for grupo, tabela in tabelas.items():
        adicionar_nos_e_arestas(grafo, tabela, grupo)

    return grafo

# Layout e título
st.markdown(CSS_ESTILO, unsafe_allow_html=True)
st.markdown('<h1 class="centered-title">🌟 Comparar IDs Relacionados</h1>', unsafe_allow_html=True)

# Obter DataFrame
familia_df = st.session_state.get("familia_df")
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados corretamente.")
else:
    familia_df = st.session_state["familia_df"]
    col1, col2 = st.columns(2)
    with col1:
        id_selecionado_1 = st.text_input("Digite o primeiro ID:", placeholder="Exemplo: 100")
    with col2:
        id_selecionado_2 = st.text_input("Digite o segundo ID:", placeholder="Exemplo: 200")

    if st.button("Exibir IDs Relacionados"):
        try:
            if not id_selecionado_1.isdigit() or not id_selecionado_2.isdigit():
                st.error("Por favor, insira IDs válidos (números).")
                st.stop()

            id_selecionado_1, id_selecionado_2 = int(id_selecionado_1), int(id_selecionado_2)

            # Processar IDs
            ids_relacionados_1 = processar_id(familia_df, id_selecionado_1)
            ids_relacionados_2 = processar_id(familia_df, id_selecionado_2)
            ids_lista_normalizada = sorted(set(map(int, ids_lista)))

            ids_ambos = sorted(set(ids_relacionados_1) & set(ids_relacionados_2) & set(ids_lista_normalizada))
            ids_somente_id1 = sorted(set(ids_relacionados_1) - set(ids_relacionados_2) & set(ids_lista_normalizada))
            ids_somente_id2 = sorted(set(ids_relacionados_2) - set(ids_relacionados_1) & set(ids_lista_normalizada))
            ids_nenhum = sorted(set(ids_lista_normalizada) - set(ids_relacionados_1) - set(ids_relacionados_2))

            # Buscar nomes completos
            tabela_ambos = buscar_nomes_por_ids(familia_df, ids_ambos)
            tabela_somente_id1 = buscar_nomes_por_ids(familia_df, ids_somente_id1)
            tabela_somente_id2 = buscar_nomes_por_ids(familia_df, ids_somente_id2)
            tabela_nenhum = buscar_nomes_por_ids(familia_df, ids_nenhum)

            # Adicionar nomes dos IDs inseridos
            nome_completo_id1 = (
                familia_df.loc[familia_df.index == id_selecionado_1, "Nome Completo"].values[0]
                if id_selecionado_1 in familia_df.index
                else "Desconhecido"
            )
            nome_completo_id2 = (
                familia_df.loc[familia_df.index == id_selecionado_2, "Nome Completo"].values[0]
                if id_selecionado_2 in familia_df.index
                else "Desconhecido"
            )

            # Exibir tabelas com ID como índice
            col1, col2, col3, col4 = st.columns(4)  # Mantém proporções iguais para todas as colunas
            with col1:
                st.markdown('<div class="custom-subheader">Relacionados a Ambos</div>', unsafe_allow_html=True)
                st.dataframe(tabela_ambos.set_index("ID"), height=ALTURA_DATAFRAME, width=300)  # Definir "ID" como índice
                st.markdown(f'<div class="info-quant">Quantidade: {len(tabela_ambos)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="info-text">Matchs que estão ligados a ambos os IDs selecionados.</div>', unsafe_allow_html=True)

            with col2:
                st.markdown(f'<div class="custom-subheader">Ligados a {nome_completo_id1}</div>', unsafe_allow_html=True)
                st.dataframe(tabela_somente_id1.set_index("ID"), height=ALTURA_DATAFRAME, width=300)  # Definir "ID" como índice
                st.markdown(f'<div class="info-quant">Quantidade: {len(tabela_somente_id1)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="info-text">Matchs que estão ligados a {nome_completo_id1}.</div>', unsafe_allow_html=True)

            with col3:
                st.markdown(f'<div class="custom-subheader">Ligados a {nome_completo_id2}</div>', unsafe_allow_html=True)
                st.dataframe(tabela_somente_id2.set_index("ID"), height=ALTURA_DATAFRAME, width=300)  # Definir "ID" como índice
                st.markdown(f'<div class="info-quant">Quantidade: {len(tabela_somente_id2)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="info-text">Matchs que estão ligados a {nome_completo_id2}.</div>', unsafe_allow_html=True)

            with col4:
                st.markdown('<div class="custom-subheader">Não Relacionados</div>', unsafe_allow_html=True)
                st.dataframe(tabela_nenhum.set_index("ID"), height=ALTURA_DATAFRAME, width=300)  # Definir "ID" como índice
                st.markdown(f'<div class="info-quant">Quantidade: {len(tabela_nenhum)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="info-text">Matchs que não estão relacionados a {nome_completo_id1} e {nome_completo_id2}.</div>', unsafe_allow_html=True)


            st.divider()

            # # Criar grafo
            # tabelas = {"Ambos": tabela_ambos, "Somente ID1": tabela_somente_id1, "Somente ID2": tabela_somente_id2, "Nenhum": tabela_nenhum}
            # grafo = criar_grafo_com_nomes(tabelas)

            # pos = nx.spring_layout(grafo, seed=42)
            # edge_x, edge_y, node_x, node_y, node_colors, node_texts = [], [], [], [], [], []

            # for edge in grafo.edges():
            #     x0, y0 = pos[edge[0]]
            #     x1, y1 = pos[edge[1]]
            #     edge_x += [x0, x1, None]
            #     edge_y += [y0, y1, None]

            # for node in grafo.nodes():
            #     x, y = pos[node]
            #     node_x.append(x)
            #     node_y.append(y)
            #     group = grafo.nodes[node].get("group", "Nenhum")
            #     node_colors.append(CORES_GRAFO[group])
            #     node_texts.append(node)

            # edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.5, color="gray"))
            # node_trace = go.Scatter(
            #     x=node_x, y=node_y, mode='markers+text',
            #     marker=dict(size=15, color=node_colors, line=dict(width=1)),
            #     text=node_texts,
            #     textposition="top center"
            # )

            # fig = go.Figure(data=[edge_trace, node_trace])
            # fig.update_layout(title="Grafo com Nomes dos Resultados", showlegend=False, margin=dict(b=0, l=0, r=0, t=40))
            # st.plotly_chart(fig)

        except Exception as e:
            st.error(f"Erro ao gerar a comparação: {e}")
