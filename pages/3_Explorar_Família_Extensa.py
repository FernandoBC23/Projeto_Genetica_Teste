import streamlit as st
from helpers import (
    imprimir_familia_extensa,
)
import pandas as pd

# Configuração da página
# st.set_page_config(page_title="Árvore Genealógica", layout="wide")

# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados corretamente. Certifique-se de carregar os dados na página principal.")
else:
    familia_df = st.session_state["familia_df"]

    # Visualizar Família Extensa
    st.write("### 🌟 Visualizar Família Extensa")

    # Criar duas Colunas
    col1, col2 = st.columns(2)
    
    with col1:
        # Escolher o método de busca
        metodo_busca = st.selectbox(
            "Escolha o método de busca:",
            ["ID", "Identificador", "Nome Completo"],
        )
        
    with col2:
            # Entrada para busca
        termo_busca = st.text_input(
            f"Digite o {metodo_busca} para visualizar a árvore genealógica:",
            placeholder=f"Exemplo: {180 if metodo_busca == 'ID' else 'G5H3-8TB' if metodo_busca == 'Identificador' else 'José Altenhofen'}",
        )


    if st.button("Exibir Família Extensa", key="btn_exibir_familia"):
        try:
            # Verificar e identificar a entrada
            if metodo_busca == "ID":
                id_selecionado = int(termo_busca)
            elif metodo_busca == "Identificador":
                filtro = familia_df["Identificador"] == termo_busca
                if filtro.any():
                    id_selecionado = familia_df[filtro].index[0]
                else:
                    st.warning("Nenhuma correspondência encontrada para o Identificador informado.")
                    st.stop()
            else:  # Nome Completo
                filtro = familia_df["Nome Completo"].str.contains(termo_busca, case=False, na=False)
                if filtro.any():
                    id_selecionado = familia_df[filtro].index[0]
                else:
                    st.warning("Nenhuma correspondência encontrada para o Nome Completo informado.")
                    st.stop()

            # Capturar o resultado da função
            from io import StringIO
            import sys

            # Redirecionar saída do terminal para capturar `print`
            buffer = StringIO()
            sys.stdout = buffer

            # Chamar a função
            imprimir_familia_extensa(familia_df, id_selecionado)

            # Restaurar saída padrão e capturar o texto
            sys.stdout = sys.__stdout__
            resultado = buffer.getvalue()
            buffer.close()

            # Exibir o resultado
            if resultado.strip():
                st.markdown(f"### 🌟 Árvore genealógica para o ID: **{id_selecionado}**")
                for section in resultado.strip().split("\n\n"):  # Dividir por seções
                    # Separar título e conteúdo
                    linhas = section.strip().split("\n")
                    titulo = linhas[0]
                    conteudo = linhas[1:]

                    # Estilizar título da seção
                    st.markdown(
                        f"""
                        <div style="color: #ffffff; font-weight: bold; font-size: 18px; margin-bottom: 10px;">
                            {titulo}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Exibir conteúdo formatado
                    if conteudo:
                        for linha in conteudo:
                            if linha.startswith("ID:"):
                                # Dividir e exibir em formato limpo
                                id_nome = linha.replace("ID:", "").split(", Nome:")
                                if len(id_nome) == 2:
                                    id_formatado, nome_formatado = id_nome
                                    st.markdown(
                                        f"""
                                        <div style="background-color: #1e1e1e; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                                            <strong>ID:</strong> {id_formatado.strip()} | <strong>Nome:</strong> {nome_formatado.strip()}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(f"- {linha.strip()}")
                            else:
                                st.markdown(f"- {linha.strip()}")
                    else:
                        st.markdown("- Nenhum parente encontrado.")

                    # Adicionar divisor entre seções
                    st.divider()
            else:
                st.warning(f"Nenhuma família extensa encontrada para o ID: {id_selecionado}.")
        except Exception as e:
            st.error(f"Erro ao gerar a árvore genealógica: {e}")
