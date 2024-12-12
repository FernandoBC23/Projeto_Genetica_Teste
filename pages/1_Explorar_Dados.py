import streamlit as st

# st.set_page_config(page_title="Base de Dados Genealógicas", layout="wide")



# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")

# Título principal
st.write("### 📋 Base de Dados Genealógicas")
st.markdown("""Nesta página, você pode visualizar e filtrar os dados genealógicos carregados.""")

if familia_df is not None:
    # Barra lateral para filtros
    with st.sidebar:
        st.header("Filtros")
        
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
