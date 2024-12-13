import pandas as pd
import streamlit as st
from helpers import (
    imprimir_familia_extensa,
)

# CSS para ajustar o layout e melhorar visualização
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 1rem;
        }
        .centered-title {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #DAEAB5;
        }
        .centered-description {
            text-align: center;
            font-size: 16px;
            margin-bottom: 5px;
            color: #D9D3CC;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título e descrição centralizados
st.markdown('<h1 class="centered-title">🌟 Visualizar Família Extensa</h1>', unsafe_allow_html=True)
st.markdown('<p class="centered-description">Adicionar uma descrição do que pode ser feito nesta página.</p>', unsafe_allow_html=True)
st.divider()

# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados corretamente. Certifique-se de carregar os dados na página principal.")
else:
    familia_df = st.session_state["familia_df"]

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

            # Obter o nome e o identificador associados ao ID selecionado
            nome_selecionado = familia_df.at[id_selecionado, "Nome Completo"]
            identificador_selecionado = familia_df.at[id_selecionado, "Identificador"]

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

           
            # Adicionar o Identificador no resultado das seções
            if resultado.strip():
                # Exibir o título com nome, ID e identificador
                st.markdown(
                    f"##### 🌟 Família Extensa: **{nome_selecionado} (ID: {id_selecionado} | Identificador: {identificador_selecionado})**"
                )
                for section in resultado.strip().split("\n\n"):  # Dividir por seções
                    linhas = section.strip().split("\n")
                    titulo = linhas[0]
                    conteudo = linhas[1:]

                    # Usar expander para a seção
                    with st.expander(f"📂 {titulo}", expanded=False):
                        if conteudo:
                            for linha in conteudo:
                                linha_formatada = linha.strip()
                                
                                if linha_formatada.startswith("ID:"):
                                    # Dividir a linha corretamente
                                    try:
                                        partes = linha_formatada.split(", Nome:")
                                        id_part = partes[0].replace("ID:", "").strip()  # ID extraído
                                        nome_part = partes[1].split(", Identificador:")[0].strip()  # Nome extraído
                                        identificador_part = partes[1].split(", Identificador:")[1].strip()  # Identificador extraído
                                    except IndexError:
                                        nome_part = "Desconhecido"
                                        id_part = "Desconhecido"
                                        identificador_part = "Desconhecido"

                                    # Formatar com estilo
                                    st.markdown(
                                        f"""
                                        <div style="background: #1C2833; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                                            <p style="font-size: 14px; color: #EAECEE; margin: 0;">
                                                <strong style="color: #3498DB;">🆔 ID:</strong> {id_part}<br>
                                                <strong style="color: #3498DB;">👤 Nome:</strong> {nome_part}<br>
                                                <strong style="color: #3498DB;">🏷️ Identificador:</strong> {identificador_part}
                                            </p>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    # Formatar linhas genéricas
                                    st.markdown(f"<p style='color: #95A5A6; margin: 0;'>{linha_formatada}</p>", unsafe_allow_html=True)
                        else:
                            st.markdown("<p style='color: #E74C3C;'>Nenhum parente encontrado.</p>", unsafe_allow_html=True)
            else:
                st.warning(f"Nenhuma família extensa encontrada para o ID: {id_selecionado}.")





        except Exception as e:
            st.error(f"Erro ao gerar a árvore genealógica: {e}")
