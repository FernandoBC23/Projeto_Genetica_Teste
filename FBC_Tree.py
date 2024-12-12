import streamlit as st
from PIL import Image
import pandas as pd

st.set_page_config(
    page_title="FBC Tree",
    page_icon="🌳",
    layout="wide"
)

st.write("## FBC Tree - Análise Genealógica")
st.markdown("""
Bem-vindo ao sistema de análise genealógica! Utilize o menu à esquerda para navegar pelas páginas.
""")

# Função para redimensionar a imagem
def redimensionar_imagem(caminho, largura=None, altura=None):
    try:
        imagem = Image.open(caminho)
        if largura and altura:
            imagem = imagem.resize((largura, altura))
        elif largura:
            proporcao = largura / imagem.width
            nova_altura = int(imagem.height * proporcao)
            imagem = imagem.resize((largura, nova_altura))
        elif altura:
            proporcao = altura / imagem.height
            nova_largura = int(imagem.width * proporcao)
            imagem = imagem.resize((nova_largura, altura))
        return imagem
    except FileNotFoundError:
        st.error("Imagem não encontrada. Certifique-se de que o caminho está correto.")
        return None

# Tentar redimensionar e exibir a imagem
caminho_imagem = "imagens/capa_fbc_tree.webp"
largura_desejada = 600  # Ajuste a largura desejada
altura_desejada = 400  # Ajuste a altura desejada

imagem_redimensionada = redimensionar_imagem(caminho_imagem, largura=largura_desejada, altura=altura_desejada)

if imagem_redimensionada:
    st.image(imagem_redimensionada, caption="FBC Tree - Análise Genealógica", use_container_width=False)

# Função para carregar os dados
def carregar_dados(caminho):
    try:
        df = pd.read_excel(caminho)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]  # Remove colunas sem nome
        if "ID" in df.columns:
            df["ID"] = pd.to_numeric(df["ID"], errors="coerce", downcast="integer")  # Converte ID para inteiro
            df = df.set_index("ID")  # Define ID como índice
        return df
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {caminho}")
        return None

# Carregar dados na sessão
if "familia_df" not in st.session_state:
    st.session_state["familia_df"] = carregar_dados("datasets/Dados_Genera_MyHeritage_Arvore.xlsx")

if st.session_state["familia_df"] is not None:
    st.success("Dados carregados com sucesso! Navegue até a página 'Dados' para visualizar.")
else:
    st.error("Erro ao carregar os dados. Verifique se o arquivo está disponível.")
