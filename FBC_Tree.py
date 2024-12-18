import streamlit as st
from PIL import Image
import base64
import pandas as pd
from io import BytesIO  # Import necessário para BytesIO

# Configuração da página
st.set_page_config(
    page_title="FBC Tree",
    page_icon="🌳",
    layout="wide"
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
            margin-bottom: 10px;
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
st.markdown('<h1 class="centered-title">FBC Tree - Análise Genealógica</h1>', unsafe_allow_html=True)
st.markdown('<p class="centered-description">Bem-vindo ao sistema de análise genealógica! Utilize o menu à esquerda para navegar pelas páginas.</p>', unsafe_allow_html=True)

# Função para redimensionar a imagem e convertê-la para base64
def redimensionar_e_converter_para_base64(caminho, largura=None, altura=None):
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

        # Converter a imagem para base64
        buffer = BytesIO()
        imagem.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return img_base64
    except FileNotFoundError:
        st.error("Imagem não encontrada. Certifique-se de que o caminho está correto.")
        return None

# Tentar redimensionar, converter e exibir a imagem
caminho_imagem = "imagens/capa_fbc_tree.webp"
largura_desejada = 600  # Ajuste a largura desejada
altura_desejada = 400  # Ajuste a altura desejada

imagem_base64 = redimensionar_e_converter_para_base64(caminho_imagem, largura=largura_desejada, altura=altura_desejada)

if imagem_base64:
    image_html = f"""
    <div class="image-container">
        <img src="data:image/png;base64,{imagem_base64}" alt="FBC Tree - Análise Genealógica" style="width:auto; height:auto; max-width:100%;">
    </div>
    """
    st.markdown(image_html, unsafe_allow_html=True)

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

# Adicionar um rodapé
footer = """
<style>
footer {
    visibility: hidden;
}
.custom-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #161B22;
    color: white;
    text-align: center;
    padding: 10px 0;
    font-size: 12px;
    border-top: 1px solid #ffffff;
}
</style>
<div class="custom-footer">
    Desenvolvido por Fernando Chagas | © 2024 FBC Tree
</div>
"""
st.markdown(footer, unsafe_allow_html=True)

