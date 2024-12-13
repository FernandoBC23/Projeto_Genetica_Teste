import streamlit as st
from helpers import (
    exibir_ancestrais_comuns_por_ocorrencia,
    ids_lista,
    coletar_todos_antepassados,
    geracao_para_termo,
    obter_id_por_metodo
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
st.markdown('<h1 class="centered-title">🌳 Relatório de Ancestrais Comuns</h1>', unsafe_allow_html=True)
st.markdown('<p class="centered-description">Escolha entre gerar um relatório para um ID específico ou para todos os IDs na lista.</p>', unsafe_allow_html=True)
st.divider()

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados. Certifique-se de carregar os dados corretamente.")
else:
    familia_df = st.session_state["familia_df"]

    # Escolha entre "Um ID" ou "Todos os IDs"
    modo = st.radio("Selecione o modo:", ["ID de Referência", "Todos os IDs"], horizontal=True)

    if modo == "ID de Referência":
        id_input = st.text_input("Digite o ID de Referência:")
        if st.button("Gerar Relatório para o ID"):
            try:
                if not id_input.strip().isdigit():
                    st.error("Por favor, insira um ID válido.")
                else:
                    id_especifico = int(id_input.strip())
                    buffer = exibir_ancestrais_comuns_por_ocorrencia(familia_df, ids_lista, id_especifico)

                    st.success("Relatório gerado com sucesso!")
                    st.download_button(
                        label="📄 Baixar Relatório em PDF",
                        data=buffer,
                        file_name=f"Relatorio_Ancestrais_ID_{id_especifico}.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Erro ao gerar o relatório: {e}")

    elif modo == "Todos os IDs":
        if st.button("Gerar Relatório para Todos os IDs"):
            try:
                buffer = exibir_ancestrais_comuns_por_ocorrencia(familia_df, ids_lista)

                st.success("Relatório gerado com sucesso!")
                st.download_button(
                    label="📄 Baixar Relatório em PDF",
                    data=buffer,
                    file_name="Relatorio_Ancestrais_Todos_IDs.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro ao gerar o relatório: {e}")


     