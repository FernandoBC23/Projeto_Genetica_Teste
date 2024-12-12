import streamlit as st
import io
from io import BytesIO
from helpers import (
    exibir_antepassados_comuns_ordenados_pdf,
    ids_lista,
    coletar_todos_antepassados,
    geracao_para_termo,
    obter_id_por_metodo
)

# Verificar se o DataFrame está carregado
if "familia_df" not in st.session_state or st.session_state["familia_df"] is None:
    st.error("Os dados da família não foram carregados. Certifique-se de carregar os dados corretamente.")
else:
    familia_df_IDs = st.session_state["familia_df"]

    st.write("### 🌳 Relatório de Ancestrais Comuns")
    st.markdown(
        """
        Insira o ID, Identificador ou Nome Completo de referência abaixo para gerar e visualizar o relatório de ancestrais comuns.
        """
    )

    # Criar duas Colunas
    col1, col2 = st.columns(2)

    # Seleção do método de busca
    with col1:
        metodo_busca = st.selectbox("Escolha o método de busca:", ["ID", "Identificador", "Nome Completo"])

    with col2:
        termo_busca = st.text_input(f"Digite o {metodo_busca} de referência:")
        

    # Botão para gerar o relatório
    if st.button("Gerar Relatório"):
        try:
            # Agora a função pode ser chamada diretamente
            id_referencia = obter_id_por_metodo(metodo_busca, termo_busca, familia_df_IDs, st)

            # Filtrar a lista de IDs para não incluir o ID de referência
            ids_comparacao = [id_ for id_ in ids_lista if int(id_) != int(id_referencia)]

            # Coletar todos os antepassados do ID de referência
            antepassados_referencia = coletar_todos_antepassados(familia_df_IDs, id_referencia)

            # Gerar o conteúdo do relatório
            _, texto_relatorio = exibir_antepassados_comuns_ordenados_pdf(
                familia_df_IDs, id_referencia, ids_comparacao, retornar_texto=True
                
            )

            # Verificar se o relatório tem conteúdo
            if texto_relatorio.strip():

                 # Obter o nome da pessoa referente ao ID
                nome_pessoa = familia_df_IDs.loc[id_referencia, "Nome Completo"] if "Nome Completo" in familia_df_IDs.columns else "Desconhecido"

                st.success(f"Relatório gerado para o ID de referência: {id_referencia} | Nome: {nome_pessoa}")

                # Dividir o texto em seções para processar os ancestrais
                ancestrais = texto_relatorio.strip().split("\n\n")
                for ancestral in ancestrais:
                    # Dividir em linhas
                    linhas = ancestral.split("\n")
                    titulo = linhas[0].strip()  # O título do ancestral comum

                    # Obter o ID do ancestral comum com base nos antepassados do ID de referência
                    ancestral_id = None
                    for id_ancestral in antepassados_referencia:
                        if f"ID: {id_ancestral}" in titulo:
                            ancestral_id = id_ancestral
                            break

                    # Calcular o grau de parentesco com o ID de referência
                    grau_parentesco_referencia = antepassados_referencia.get(ancestral_id, None)
                    if grau_parentesco_referencia is not None:
                        grau_parentesco_termo = geracao_para_termo(grau_parentesco_referencia)
                        titulo += f" (Parentesco com Referência: {grau_parentesco_termo})"

                    st.markdown(
                        f"""
                        <div style="background-color: #161B22; color: #ffffff; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <strong>{titulo}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Criar uma lista de dados para exibir como tabela
                    dados_tabela = []
                    for linha in linhas[1:]:
                        partes = linha.split(", ")
                        if len(partes) == 3:  # Verificar se a linha está no formato esperado
                            dados_tabela.append(partes)

                    # Verificar se há dados para exibir
                    if dados_tabela:
                        # Exibir a tabela com os dados
                        st.table(
                            {
                                "ID": [row[0] for row in dados_tabela],
                                "Nome": [row[1] for row in dados_tabela],
                                "Grau": [row[2] for row in dados_tabela],
                            }
                        )
                    # else:
                        # st.warning("Nenhum dado encontrado para este ancestral comum.")
                        # st.divider()  # Adicionar um divisor entre ancestrais


                # Adicionar botão para download do PDF                
                buffer = io.BytesIO()
                exibir_antepassados_comuns_ordenados_pdf(
                    familia_df_IDs, id_referencia, ids_comparacao, retornar_texto=False, output_buffer=buffer
                )
                buffer.seek(0)

                # Obter o nome da pessoa referente ao ID
                nome_pessoa = familia_df_IDs.loc[id_referencia, "Nome Completo"] if "Nome Completo" in familia_df_IDs.columns else "Desconhecido"

                # Garantir que o nome está seguro para uso no nome do arquivo
                nome_pessoa_seguro = nome_pessoa.replace(" ", "_").replace("/", "_").replace("\\", "_")

                # Botão de download
                st.download_button(
                    label="📄 Baixar Relatório em PDF",
                    data=buffer,
                    file_name=f"Relatorio Ancestrais - ID: {id_referencia} Nome: {nome_pessoa_seguro}.pdf",
                    mime="application/pdf"
                    
                )
            else:
                st.warning(f"Nenhum ancestral comum encontrado para o ID de referência {id_referencia}.")
        except Exception as e:
            st.error(f"Erro ao gerar o relatório: {e}")
