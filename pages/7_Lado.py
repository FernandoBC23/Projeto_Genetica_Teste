import pandas as pd
import re
import streamlit as st
import networkx as nx

from helpers import (
    imprimir_familia_extensa,  # Função para gerar família extensa
    ids_lista,  # Lista de IDs para comparação
)

# Configurações globais
ALTURA_DATAFRAME = 360
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

def categorizar_ramos(familia_df, relacoes_iniciais, ids_lista):
    """Classifica IDs em ramos genealógicos."""
    categorias = relacoes_iniciais.copy()

    for id_ in ids_lista:
        if id_ in categorias:
            continue
        relacionados = processar_id(familia_df, id_)
        ramos_relacionados = {categorias.get(rel, "Indefinido") for rel in relacionados}
        ramos_relacionados.discard("Indefinido")

        if len(ramos_relacionados) == 1:
            categorias[id_] = list(ramos_relacionados)[0]
        else:
            categorias[id_] = "Indefinido"

    return categorias

# Layout e título
st.markdown(CSS_ESTILO, unsafe_allow_html=True)
st.markdown('<h1 class="centered-title">🌟 Classificar Ramos Genealógicos</h1>', unsafe_allow_html=True)

familia_df = st.session_state.get("familia_df")

if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados corretamente.")
else:
    familia_df = st.session_state["familia_df"]

    relacoes_iniciais = st.text_input(
        "Relações iniciais (Ex.: 100:Paterno, 200:Materno)",
        placeholder="Digite IDs e ramos separados por vírgula"
    )

    if st.button("Classificar Ramos"):
        try:
            if not relacoes_iniciais.strip():
                st.error("Por favor, forneça relações iniciais.")
                st.stop()

            relacoes_iniciais = {
                int(k): v for k, v in (
                    rel.split(":") for rel in relacoes_iniciais.split(",") if ":" in rel
                )
            }

            categorias = categorizar_ramos(familia_df, relacoes_iniciais, ids_lista)

            # Adicionar nomes completos aos resultados
            resultados_df = pd.DataFrame([
                {"ID": id_, "Ramo": ramo} for id_, ramo in categorias.items()
            ])
            resultados_df = resultados_df.merge(
                buscar_nomes_por_ids(familia_df, resultados_df["ID"]),
                on="ID", how="left"
            )

            # Dividir por categoria
            df_paternos = resultados_df[resultados_df["Ramo"] == "Paterno"]
            df_maternos = resultados_df[resultados_df["Ramo"] == "Materno"]
            df_indefinidos = resultados_df[resultados_df["Ramo"] == "Indefinido"]

            # Exibir os resultados em colunas
            col1, col2, col3 = st.columns([1, 1, 1])  # Proporções iguais

            with col1:
                st.markdown('<div class="custom-subheader">Paternos</div>', unsafe_allow_html=True)
                st.dataframe(df_paternos.set_index("ID"), height=ALTURA_DATAFRAME, width=300)
                st.markdown(f'<div class="info-quant">Quantidade: {len(df_paternos)}</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="custom-subheader">Maternos</div>', unsafe_allow_html=True)
                st.dataframe(df_maternos.set_index("ID"), height=ALTURA_DATAFRAME, width=300)
                st.markdown(f'<div class="info-quant">Quantidade: {len(df_maternos)}</div>', unsafe_allow_html=True)

            with col3:
                st.markdown('<div class="custom-subheader">Indefinidos</div>', unsafe_allow_html=True)
                st.dataframe(df_indefinidos.set_index("ID"), height=ALTURA_DATAFRAME, width=300)
                st.markdown(f'<div class="info-quant">Quantidade: {len(df_indefinidos)}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao classificar os ramos: {e}")
