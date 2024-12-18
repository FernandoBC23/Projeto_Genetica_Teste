import streamlit as st
from helpers import (
    exibir_ancestrais_comuns_por_ocorrencia,
    gerar_relatorio_visualizacao,
    ids_lista,
    obter_id_por_metodo  # Função para processar os métodos de busca
)

# CSS para ajustar o layout
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 1rem;
        }
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
    </style>
    """, unsafe_allow_html=True)

# Título e descrição centralizados
st.markdown('<h1 class="centered-title">🌳 Relatório de Ancestrais Comuns</h1>', unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center;
                font-size: 16px;
                color: #D9D3CC;
                margin-top: 10px;
                margin-bottom: 20px;
                line-height: 1.5;">
        Gere um <strong>relatório de ancestrais comuns</strong> com base em um membro específico ou em todos os IDs disponíveis.
        <br><br>
        </strong>Pré-visualização</strong> do relatório e oferece a opção de <strong>download em PDF</strong> 
        para facilitar a análise e o armazenamento dos dados.
    </div>
""", unsafe_allow_html=True)

st.divider()

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados. Certifique-se de carregar os dados corretamente.")
else:
    familia_df_IDs = st.session_state["familia_df"]

    # Seleção do método de busca
    col1, col2 = st.columns(2)
    with col1:
        metodo_busca = st.selectbox("Escolha o método de busca:", ["ID", "Identificador", "Nome Completo"])
    with col2:
        termo_busca = st.text_input(f"Digite o {metodo_busca} de referência:")

    # Escolha entre "Relatório por ID" ou "Todos os IDs"
    col3, col4 = st.columns(2)
    with col3:
        tipo_relatorio = st.radio("Selecione o tipo de relatório:", ["Relatório por ID", "Todos os IDs"], horizontal=True)

    # Geração do relatório
    if tipo_relatorio == "Relatório por ID" and st.button("Gerar Relatório"):
        try:
            # Obter o ID de referência com base no método de busca
            id_referencia = obter_id_por_metodo(metodo_busca, termo_busca, familia_df_IDs, st)

            # Gerar o conteúdo visual do relatório
            st.success(f"Relatório gerado para o ID de referência: {id_referencia}")
            relatorio_visual = gerar_relatorio_visualizacao(familia_df_IDs, ids_lista, id_referencia)
            st.markdown(relatorio_visual, unsafe_allow_html=True)

            # Gerar o PDF
            buffer = exibir_ancestrais_comuns_por_ocorrencia(familia_df_IDs, ids_lista, id_referencia)
            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=buffer,
                file_name=f"Relatorio_Ancestrais_ID_{id_referencia}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar o relatório: {e}")

    elif tipo_relatorio == "Todos os IDs" and st.button("Gerar Relatório para Todos os IDs"):
        try:
            # Gerar relatório para todos os IDs
            buffer = exibir_ancestrais_comuns_por_ocorrencia(familia_df_IDs, ids_lista)
            texto_relatorio = gerar_relatorio_visualizacao(familia_df_IDs, ids_lista)

            st.text_area("Pré-visualização do Relatório", texto_relatorio, height=400)

            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=buffer,
                file_name="Relatorio_Ancestrais_Todos_IDs.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar o relatório: {e}")
