import pandas as pd
import re
import streamlit as st
from io import BytesIO
from PyPDF2 import PdfReader
from helpers import exibir_ancestrais_comuns_por_ocorrencia, buscar_nome_sobrenome_por_id, ids_lista, obter_id_por_metodo

# Função para extrair IDs a partir do buffer PDF usando PyPDF2
def extrair_ids_dos_descendentes(buffer):
    """Extrai IDs dos descendentes do buffer PDF."""
    buffer.seek(0)
    pdf = PdfReader(buffer)
    texto = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    ids_encontrados = set(re.findall(r"ID:\s*(\d+)", texto))
    return set(map(int, ids_encontrados))

# Função para buscar nomes por lista de IDs
def buscar_nomes_para_lista(df, ids):
    """Aplica buscar_nome_sobrenome_por_id a uma lista de IDs."""
    if not ids:  # Se a lista estiver vazia
        return pd.DataFrame(columns=["ID", "Nome Completo"])
    resultado = [{"ID": id_, "Nome Completo": buscar_nome_sobrenome_por_id(df, id_)} for id_ in ids]
    return pd.DataFrame(resultado)

# Função para processar todos os IDs da lista de matches
def processar_lista_de_matches(df, ids_lista, ids_ancestrais_ref1, ids_ancestrais_ref2):
    """Processa todos os IDs da lista de matches e os categoriza em 4 grupos."""
    ids_ambos = set()
    ids_somente_id1 = set()
    ids_somente_id2 = set()
    ids_nenhum = set()

    for id_match in ids_lista:
        buffer_match = exibir_ancestrais_comuns_por_ocorrencia(df, ids_lista, id_match)
        ids_ancestrais_match = extrair_ids_dos_descendentes(buffer_match)

        if ids_ancestrais_match & ids_ancestrais_ref1 and ids_ancestrais_match & ids_ancestrais_ref2:
            ids_ambos.add(id_match)
        elif ids_ancestrais_match & ids_ancestrais_ref1:
            ids_somente_id1.add(id_match)
        elif ids_ancestrais_match & ids_ancestrais_ref2:
            ids_somente_id2.add(id_match)
        else:
            ids_nenhum.add(id_match)

    return ids_ambos, ids_somente_id1, ids_somente_id2, ids_nenhum

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
    """,
    unsafe_allow_html=True,
)

# Título e descrição centralizados
st.markdown('<h1 class="centered-title">🔎 Comparação de IDs Relacionados com a Lista de Matches</h1>', unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center;
                font-size: 16px;
                color: #D9D3CC;
                margin-top: 10px;
                margin-bottom: 20px;
                line-height: 1.5;">
        Compare dois indivíduos e analise como eles estão <strong>relacionados</strong> com os membros de uma lista pré definida de matches. 
    </div>
""", unsafe_allow_html=True)

st.divider()

# Recuperar DataFrame
familia_df = st.session_state.get("familia_df")

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados corretamente. Certifique-se de carregar os dados na página principal.")
else:
    familia_df = st.session_state["familia_df"]


    # Seleção do método de busca e termos
    col1, col2, col3 = st.columns(3)
    with col1:
        metodo_busca = st.selectbox("Método de busca:", ["ID", "Identificador", "Nome Completo"], key="metodo_busca")
    with col2:
        termo_busca1 = st.text_input(f"Digite o {metodo_busca} da Pessoa 1:", key="termo_busca1")
    with col3:
        termo_busca2 = st.text_input(f"Digite o {metodo_busca} da Pessoa 2:", key="termo_busca2")

    # Botão para processar
    if st.button("Processar IDs da Lista de Matches"):
        try:
            # Obter IDs de referência
            id1 = obter_id_por_metodo(metodo_busca, termo_busca1, familia_df, st)
            id2 = obter_id_por_metodo(metodo_busca, termo_busca2, familia_df, st)

            if id1 == id2:
                st.error("Por favor, informe IDs diferentes.")
                st.stop()

            # Obter nomes associados aos IDs
            nome_id1 = buscar_nome_sobrenome_por_id(familia_df, id1)
            nome_id2 = buscar_nome_sobrenome_por_id(familia_df, id2)

            # Buscar ancestrais dos IDs de referência
            buffer_id1 = exibir_ancestrais_comuns_por_ocorrencia(familia_df, ids_lista, id1)
            buffer_id2 = exibir_ancestrais_comuns_por_ocorrencia(familia_df, ids_lista, id2)

            ids_ancestrais_ref1 = extrair_ids_dos_descendentes(buffer_id1)
            ids_ancestrais_ref2 = extrair_ids_dos_descendentes(buffer_id2)

            # Processar IDs da lista de matches
            ids_ambos, ids_somente_id1, ids_somente_id2, ids_nenhum = processar_lista_de_matches(
                familia_df, ids_lista, ids_ancestrais_ref1, ids_ancestrais_ref2
            )

            # Criar tabelas
            tabela_ambos = buscar_nomes_para_lista(familia_df, ids_ambos)
            tabela_id1 = buscar_nomes_para_lista(familia_df, ids_somente_id1)
            tabela_id2 = buscar_nomes_para_lista(familia_df, ids_somente_id2)
            tabela_nenhum = buscar_nomes_para_lista(familia_df, ids_nenhum)

            # Exibição dos resultados em 4 colunas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div class="result-title">🔗 Ambos</div>', unsafe_allow_html=True)
                st.dataframe(tabela_ambos.set_index("ID"))
                st.markdown(f"**Quantidade:** {len(tabela_ambos)}")
            with col2:
                st.markdown(f'<div class="result-title">🔍 Apenas {nome_id1}</div>', unsafe_allow_html=True)
                st.dataframe(tabela_id1.set_index("ID"))
                st.markdown(f"**Quantidade:** {len(tabela_id1)}")
            with col3:
                st.markdown(f'<div class="result-title">🔍 Apenas {nome_id2}</div>', unsafe_allow_html=True)
                st.dataframe(tabela_id2.set_index("ID"))
                st.markdown(f"**Quantidade:** {len(tabela_id2)}")
            with col4:
                st.markdown('<div class="result-title">🚫 Não Relacionados</div>', unsafe_allow_html=True)
                st.dataframe(tabela_nenhum.set_index("ID"))
                st.markdown(f"**Quantidade:** {len(tabela_nenhum)}")

        except Exception as e:
            st.error(f"Erro ao processar os IDs: {e}")
