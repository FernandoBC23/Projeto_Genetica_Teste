import streamlit as st

# CSS para ajustar o layout
st.markdown("""
    <style>
        /* Remove o espaçamento padrão da página */
        .block-container {
            padding-top: 1rem; /* Espaçamento superior */
            padding-bottom: 1rem; /* Espaçamento inferior */
        }

        /* Centralizar título, descrição e imagem */
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
        .image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# Título e descrição centralizados
st.markdown('<h1 class="centered-title">📋 Base de Dados Genealógicas</h1>', unsafe_allow_html=True)
st.markdown('<p class="centered-description">Nesta página, você pode visualizar e filtrar os dados genealógicos carregados.</p>', unsafe_allow_html=True)
st.divider()

# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")


if familia_df is not None:
    # Barra lateral para filtros
    
    st.subheader("Filtros")
        
    # Filtro de busca por texto
    texto_procurado = st.text_input(
        "Buscar por Nome, Sobrenome, Identificador ou Nome Completo:",
        placeholder="Exemplo: José, Altenhofen, G5H3-8TB"
    )
        
    # Selecionar colunas para exibição
    colunas_disponiveis = familia_df.columns.tolist()
    colunas_selecionadas = st.multiselect(
        "Selecione as colunas que deseja exibir:",
        options=colunas_disponiveis,
        default=colunas_disponiveis[:4],
    )

    # Aplicar os filtros
    resultados = familia_df.copy()
    if texto_procurado:
        resultados = resultados[resultados.apply(
            lambda row: row.astype(str).str.contains(texto_procurado, case=False, na=False).any(),
            axis=1
        )]

    # Exibir os dados filtrados
    if not resultados.empty:
        st.success(f"{len(resultados)} registros encontrados.")
        st.dataframe(resultados[colunas_selecionadas], use_container_width=True)
    else:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")
else:
    st.error("Os dados não foram carregados corretamente. Verifique a página inicial.")
