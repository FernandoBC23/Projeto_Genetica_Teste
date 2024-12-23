import pandas as pd
import streamlit as st
from helpers import (
    buscar_nome_sobrenome_por_id,
    encontrar_parentesco_direto,
    buscar_id_no_dicionario,
    geracao_para_termo,
    coletar_todos_antepassados,
)

# CSS para ajustar o layout
st.markdown("""
    <style>
        /* Remove o espaçamento padrão da página */
        .block-container {
            padding-top: 1.3rem; /* Espaçamento superior */
            padding-bottom: 1rem; /* Espaçamento inferior */
        }

        /* Centralizar título, descrição e imagem */
        .centered-title {
            text-align: center;
            font-size: 28px;
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
        .image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# Título e descrição centralizados
st.markdown('<h1 class="centered-title">👨‍👩‍👧 Comparador de Parentesco e Análise de Antepassados</h1>', unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center;
                font-size: 16px;
                color: #D9D3CC;
                margin-top: 10px;
                margin-bottom: 20px;
                line-height: 1.5;">
        Compare o <strong>grau de parentesco</strong> entre dois membros da família e identifique os 
        <strong>antepassados comuns</strong>. 
        <br><br>
        A análise exibe de forma estruturada os <strong>parentescos diretos</strong> e os 
        <strong>antepassados compartilhados</strong> entre os membros selecionados, facilitando o 
        entendimento das conexões familiares.
    </div>
""", unsafe_allow_html=True)

st.divider()

# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")

# Função para obter o ID a partir do método de busca
def obter_id_por_metodo(metodo_busca, termo_busca, familia_df):
    try:
        if metodo_busca == "ID":
            return int(termo_busca)
        elif metodo_busca == "Identificador":
            filtro = familia_df["Identificador"] == termo_busca
            ids_encontrados = familia_df[filtro].index.tolist()
            if len(ids_encontrados) == 1:
                return ids_encontrados[0]
            elif len(ids_encontrados) > 1:
                st.warning(f"Mais de um resultado encontrado para o Identificador '{termo_busca}'. Selecione um ID específico.")
                st.stop()
            else:
                st.warning(f"Nenhuma correspondência encontrada para o Identificador '{termo_busca}'.")
                st.stop()
        elif metodo_busca == "Nome Completo":
            filtro = familia_df["Nome Completo"].str.contains(termo_busca, case=False, na=False)
            ids_encontrados = familia_df[filtro].index.tolist()
            if len(ids_encontrados) == 1:
                return ids_encontrados[0]
            elif len(ids_encontrados) > 1:
                st.warning(f"Mais de um resultado encontrado para o Nome '{termo_busca}'. Selecione um ID específico.")
                st.stop()
            else:
                st.warning(f"Nenhuma correspondência encontrada para o Nome Completo '{termo_busca}'.")
                st.stop()
    except Exception as e:
        st.error(f"Erro ao buscar ID: {e}")
        st.stop()

# Verifica se o DataFrame está carregado
if "familia_df" in st.session_state and st.session_state.familia_df is not None:
    familia_df = st.session_state.familia_df

    # Inputs para os dois termos de busca
    col1, col2, col3 = st.columns(3)
    with col1:
        metodo_busca = st.selectbox("Método de busca:", ["ID", "Identificador", "Nome Completo"], key="metodo_busca")
    with col2:
        termo_busca1 = st.text_input(f"Digite o {metodo_busca} da Pessoa 1:", key="termo_busca1")
    with col3:
        termo_busca2 = st.text_input(f"Digite o {metodo_busca} da Pessoa 2:", key="termo_busca2")

    # Botão para executar ambas as funcionalidades
    if st.button("Executar Comparação e Análise de Antepassados"):
        try:
            # Obter os IDs a partir do método e termo de busca
            id1 = obter_id_por_metodo(metodo_busca, termo_busca1, familia_df)
            id2 = obter_id_por_metodo(metodo_busca, termo_busca2, familia_df)

            if id1 == id2:
                st.error("Por favor, informe IDs diferentes.")
            else:
                # Função 1: Comparar IDs
                st.subheader("🔍 Resultado da Comparação de IDs")
                try:
                    nome_ID1 = buscar_nome_sobrenome_por_id(familia_df, id1)
                    nome_ID2 = buscar_nome_sobrenome_por_id(familia_df, id2)
                    parentescos_id1, parentescos_id2 = encontrar_parentesco_direto(familia_df, id1, id2)
                    parentesco_encontrado_1 = buscar_id_no_dicionario(parentescos_id1, id2)
                    parentesco_encontrado_2 = buscar_id_no_dicionario(parentescos_id2, id1)
                    st.success(f"{nome_ID2} é {parentesco_encontrado_1} de {nome_ID1}")
                    st.success(f"{nome_ID1} é {parentesco_encontrado_2} de {nome_ID2}")
                except Exception as e:
                    st.error(f"Erro na comparação de IDs: {e}")

                # Função 2: Analisar Antepassados em Comum
                st.subheader("🌳 Resultado da Análise de Antepassados Comuns")
                try:
                    # Executa a função e coleta os resultados
                    antepassados_id1 = coletar_todos_antepassados(familia_df, id1)
                    antepassados_id2 = coletar_todos_antepassados(familia_df, id2)

                    # Encontrando antepassados comuns
                    antepassados_comuns = {
                        antepassado: (antepassados_id1[antepassado], antepassados_id2[antepassado])
                        for antepassado in set(antepassados_id1) & set(antepassados_id2)
                    }

                    # Ordena antepassados comuns
                    antepassados_ordenados = sorted(
                        antepassados_comuns.items(), key=lambda x: x[1][0] + x[1][1]
                    )

                    # Exibe os resultados
                    if antepassados_ordenados:
                        with st.expander("Resultados dos Antepassados Comuns", expanded=True):
                            for antepassado, (grau_id1, grau_id2) in antepassados_ordenados:
                                nome_antepassado = buscar_nome_sobrenome_por_id(familia_df, antepassado)
                                st.markdown(f"""
                                **{nome_antepassado}:**
                                - {geracao_para_termo(grau_id1)} de {nome_ID1}
                                - {geracao_para_termo(grau_id2)} de {nome_ID2}
                                """)
                    else:
                        st.warning(f"Nenhum antepassado comum encontrado entre {nome_ID1} e {nome_ID2}.")
                except Exception as e:
                    st.error(f"Erro na análise de antepassados comuns: {e}")
        except Exception as e:
            st.error(f"Erro geral: {e}")
else:
    st.error("Os dados não foram carregados corretamente.")
