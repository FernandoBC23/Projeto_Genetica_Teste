import pandas as pd
import os
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from collections import defaultdict
import streamlit as st

# Função para carregar o DataFrame
def carregar_dataframe(caminho):
    """Carrega um DataFrame a partir de um arquivo Excel."""
    df = pd.read_excel(caminho)
    df.set_index('ID', inplace=True)  # Define a coluna 'ID' como índice
    return df

# Exemplo de carregamento do DataFrame
# Substitua pelo caminho real do seu arquivo de dados
caminho = pd.read_excel("datasets/Dados_Genera_MyHeritage_Arvore.xlsx")


def buscar_nome_sobrenome_por_id(df, pessoa_id):
    """Busca o nome e sobrenome de uma pessoa por ID e retorna como uma string única no campo 'Nome Completo'."""
    if pessoa_id in df.index and pessoa_id != 0:
        nome = df.at[pessoa_id, 'Nome'] if 'Nome' in df.columns and pd.notna(df.at[pessoa_id, 'Nome']) else "Desconhecido"
        sobrenome = df.at[pessoa_id, 'Sobrenome'] if 'Sobrenome' in df.columns and pd.notna(df.at[pessoa_id, 'Sobrenome']) else ""
        return f"{nome} {sobrenome}".strip()
    return "Desconhecido"

# ------------------------------------------------------------------------------------------------------------------------------------------

def encontrar_descendentes(df, pessoa_ids):
    descendentes = pd.DataFrame()
    for pessoa_id in pessoa_ids:
        pessoa_id_str = str(pessoa_id)  # Convert to string
        if pessoa_id_str.isdigit():  # Check if the ID is numeric
            pessoa_id = int(pessoa_id_str)  # Convert to integer
            if pessoa_id > 0:  # Check if the ID is valid
                # Search for children regardless of whether both parents are registered
                descendentes_temp = df[(df['Pai_ID'] == pessoa_id) | (df['Mãe_ID'] == pessoa_id)]
                descendentes = pd.concat([descendentes, descendentes_temp])
    return descendentes.drop_duplicates()



def id_valido(df, pessoa_id):
    # Verifica se o ID está no DataFrame e não é nulo
    return pessoa_id in df.index and not pd.isnull(pessoa_id) and pessoa_id > 0


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_pais(df, pessoa_id):
    if pessoa_id in df.index and pessoa_id != 0:
        pai_id = df.at[pessoa_id, 'Pai_ID'] if pd.notna(df.at[pessoa_id, 'Pai_ID']) and df.at[pessoa_id, 'Pai_ID'] in df.index else None
        mae_id = df.at[pessoa_id, 'Mãe_ID'] if pd.notna(df.at[pessoa_id, 'Mãe_ID']) and df.at[pessoa_id, 'Mãe_ID'] in df.index else None
        return {'pai': pai_id, 'mae': mae_id}
    return {'pai': None, 'mae': None}


def buscar_filhos(df, pessoa_id):
    """Busca os filhos de uma pessoa no DataFrame e retorna uma lista de dicionários."""
    filhos = df[(df['Pai_ID'] == pessoa_id) | (df['Mãe_ID'] == pessoa_id)]
    filhos = filhos.assign(ID=filhos.index)  # Método seguro para adicionar 'ID'
    lista_filhos = filhos[['ID', 'Nome', 'Sobrenome']].to_dict('records')
    return lista_filhos


def buscar_irmaos(df, pessoa_id):
    if pessoa_id not in df.index:
        print(f"O ID {pessoa_id} não foi encontrado no DataFrame.")
        return []

    # Obtém os IDs dos pais da pessoa de interesse
    pai_id = df.at[pessoa_id, 'Pai_ID']
    mae_id = df.at[pessoa_id, 'Mãe_ID']

    irmaos = pd.DataFrame()
    if pai_id > 0 and not pd.isnull(pai_id):
        irmaos_paternos = df[(df['Pai_ID'] == pai_id) & (df.index != pessoa_id)]
        irmaos = pd.concat([irmaos, irmaos_paternos])
    if mae_id > 0 and not pd.isnull(mae_id):
        irmaos_maternos = df[(df['Mãe_ID'] == mae_id) & (df.index != pessoa_id)]
        irmaos = pd.concat([irmaos, irmaos_maternos])

    irmaos = irmaos.drop_duplicates()

    # Formatação da saída
    lista_irmaos = [{'ID': idx, 'Nome Completo': f"{row['Nome']} {row['Sobrenome']}"} for idx, row in irmaos.iterrows()]
    return lista_irmaos


def buscar_sobrinhos(df, pessoa_id):
    """Busca todos os sobrinhos de uma pessoa no DataFrame."""
    irmaos = buscar_irmaos(df, pessoa_id)  # Supondo que isto retorne uma lista de dicionários

    # Lista para coletar os dicionários dos sobrinhos
    sobrinhos = []

    # Itera sobre cada irmão usando a chave 'ID' para encontrar seus filhos
    for irmao in irmaos:
        irmao_id = irmao['ID']
        filhos_do_irmao = buscar_filhos(df, irmao_id)  # Supondo que esta função já retorne uma lista de dicionários

        # Adiciona os filhos (sobrinhos) à lista de sobrinhos
        sobrinhos.extend(filhos_do_irmao)

    return sobrinhos


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_avos(df, pessoa_id):
    """Busca os IDs dos avós de uma pessoa e retorna um dicionário."""
    avos_ids = {'Avô Paterno': None, 'Avó Paterna': None, 'Avô Materno': None, 'Avó Materna': None}
    pais_ids = buscar_pais(df, pessoa_id)
    
    # Buscar os pais (pai e mãe)
    for chave, id in pais_ids.items():
        if id and id in df.index:
            # Busca o ID do pai e da mãe do pai ou mãe da pessoa
            Avo_Paterno = df.at[id, 'Pai_ID'] if 'Pai_ID' in df.columns and pd.notna(df.at[id, 'Pai_ID']) else None
            Avo_Materna = df.at[id, 'Mãe_ID'] if 'Mãe_ID' in df.columns and pd.notna(df.at[id, 'Mãe_ID']) else None
            
            # Atribuição baseada em qual pai (pai ou mãe da pessoa) está sendo considerado
            if chave == 'pai':
                avos_ids['Avô Paterno'] = Avo_Paterno
                avos_ids['Avó Paterna'] = Avo_Materna
            else:
                avos_ids['Avô Materno'] = Avo_Paterno
                avos_ids['Avó Materna'] = Avo_Materna
                
    return avos_ids


def buscar_tios(df, pessoa_id):
    """Busca e retorna os tios paternos e maternos de uma pessoa como um dicionário de listas de dicionários."""
    # Busca os IDs dos pais da pessoa
    pais = buscar_pais(df, pessoa_id)
    pai_id = pais['pai']
    mae_id = pais['mae']

    # Dicionário para armazenar os tios paternos e maternos
    tios = {
        'tios_paternos': [],
        'tios_maternos': []
    }

    # Se o ID do pai é válido, busca os irmãos do pai (tios paternos)
    if pai_id and pai_id > 0:
        tios_paternos = buscar_irmaos(df, pai_id)
        tios['tios_paternos'].extend(tios_paternos)

    # Se o ID da mãe é válido, busca os irmãos da mãe (tios maternos)
    if mae_id and mae_id > 0:
        tios_maternos = buscar_irmaos(df, mae_id)
        tios['tios_maternos'].extend(tios_maternos)

    return tios


def buscar_primos_primeiro_grau(df, pessoa_id):
    # Encontrar pais da pessoa
    pais = buscar_pais(df, pessoa_id)
    pai_id = pais['pai']
    mae_id = pais['mae']
    
    # Inicializar lista para armazenar os primos de primeiro grau
    primos_primeiro_grau = []
    
    # Verificar se existem IDs válidos para pai e mãe antes de buscar tios e tias
    if pai_id and pai_id in df.index:
        tios_paternos = buscar_irmaos(df, pai_id)
        # Para cada tio ou tia paterno, buscar seus filhos
        for tio in tios_paternos:
            filhos_do_tio = buscar_filhos(df, tio['ID'])
            primos_primeiro_grau.extend(filhos_do_tio)  # Adiciona os filhos do tio à lista de primos
    
    if mae_id and mae_id in df.index:
        tios_maternos = buscar_irmaos(df, mae_id)
        # Para cada tio ou tia materno, buscar seus filhos
        for tia in tios_maternos:
            filhos_da_tia = buscar_filhos(df, tia['ID'])
            primos_primeiro_grau.extend(filhos_da_tia)  # Adiciona os filhos da tia à lista de primos

    # Remover possíveis duplicatas baseado no ID (usando um dicionário para filtrar)
    unique_primos = {primo['ID']: primo for primo in primos_primeiro_grau}.values()

    return list(unique_primos)


def buscar_filhos_dos_primos_primeiro_grau(df, pessoa_id):
    primos = buscar_primos_primeiro_grau(df, pessoa_id)  # Retorna lista de dicionários
    filhos_dos_primos_primeiro_grau = []

    # Para cada primo, buscar seus filhos
    for primo in primos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Reutilizar a função buscar_filhos que já retorna uma lista de dicionários
        filhos_dos_primos_primeiro_grau.extend(filhos_do_primo)  # Concatenar as listas de filhos de cada primo

    # Eliminar possíveis duplicatas baseado em ID (opcional, depende dos dados)
    unique_filhos = {f['ID']: f for f in filhos_dos_primos_primeiro_grau}.values()

    return list(unique_filhos)


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_bisavos(df, pessoa_id):
    bisavos = []

    # Encontrar os avós (usa a função existente que precisa retornar IDs dos avós)
    avos = buscar_avos(df, pessoa_id)  # Aqui assume que a função buscar_avos foi ajustada para devolver um dicionário de IDs

    # Lista de IDs de avós para considerar, combinando avós paternos e maternos
    avo_ids = [avos['Avô Paterno'], avos['Avó Paterna'], avos['Avô Materno'], avos['Avó Materna']]

    # Para cada avô, encontrar seus pais (os bisavós da pessoa original)
    for avo_id in avo_ids:
        if avo_id and avo_id > 0:  # Verificando se o ID é válido
            pais_do_avo = buscar_pais(df, avo_id)
            for key, bisavo_id in pais_do_avo.items():
                if bisavo_id and bisavo_id > 0:
                    nome_bisavo = buscar_nome_sobrenome_por_id(df, bisavo_id)
                    bisavos.append({'ID': bisavo_id, 'Nome Completo': nome_bisavo})

    return bisavos



def buscar_tios_avos(df, pessoa_id):
    """Busca todos os tio-avôs e tia-avós de uma pessoa no DataFrame."""
    # Primeiro, encontrar todos os avós da pessoa usando a função ajustada buscar_avos
    avos = buscar_avos(df, pessoa_id)
    
    # Lista para manter os tios-avós
    tios_avos = []

    # Verificar cada avô e avó encontrado
    for avo_id in avos.values():
        if avo_id:  # Verificando se o avô ou avó possui um ID válido
            irmãos_do_avô = buscar_irmaos(df, avo_id)
            tios_avos.extend(irmãos_do_avô)  # Adiciona irmãos do avô à lista de tios-avós

    # Retornar lista única de tios-avós, removendo duplicatas com base em IDs
    unique_tios_avos = {tio['ID']: tio for tio in tios_avos}.values()
    return list(unique_tios_avos)


def buscar_primos_primeiro_grau_dos_pais(df, pessoa_id):
    """Busca os primos de primeiro grau dos pais da pessoa, que são os filhos dos tios-avós."""
    avos = buscar_avos(df, pessoa_id)  # Primeiro, encontrar todos os avós da pessoa
    primos_primeiro_grau_dos_pais = []

    # Para cada avô e avó, buscar os filhos dos seus irmãos (tios-avós)
    for avo_id in avos.values():
        if avo_id:  # Se o ID do avô/avó não é None
            tios_avos = buscar_irmaos(df, avo_id)
            # Para cada tio-avô ou tia-avó, buscar seus filhos
            for tio_avo in tios_avos:
                filhos_do_tio_avo = buscar_filhos(df, tio_avo['ID'])
                primos_primeiro_grau_dos_pais.extend(filhos_do_tio_avo)

    # Removendo duplicatas baseado no ID e retornando a lista final
    unique_primos = {primo['ID']: primo for primo in primos_primeiro_grau_dos_pais}.values()
    return list(unique_primos)


def buscar_primos_segundo_grau(df, pessoa_id):
    # Primeiro, obtemos os primos de primeiro grau dos pais da pessoa
    primos_primeiro_grau_dos_pais = buscar_primos_primeiro_grau_dos_pais(df, pessoa_id)
    
    # Inicializamos uma lista para armazenar os resultados
    primos_segundo_grau = []
    
    # Iteramos sobre cada primo de primeiro grau dos pais
    for primo in primos_primeiro_grau_dos_pais:
        primo_id = primo['ID']  # Supomos que cada entrada no dicionário tem um ID
        # Buscamos os filhos de cada primo
        filhos_do_primo = buscar_filhos(df, primo_id)
        # Adicionamos os filhos do primo à lista de resultados
        primos_segundo_grau.extend(filhos_do_primo)

    return primos_segundo_grau


def buscar_filhos_dos_primos_segundo_grau(df, pessoa_id):
    """Busca os filhos dos primos de segundo grau de uma pessoa."""
    primos_segundo_grau = buscar_primos_segundo_grau(df, pessoa_id)  # Obtemos a lista de primos de segundo grau
    filhos_dos_primos_segundo_grau = []

    # Para cada primo de segundo grau, buscar seus filhos
    for primo in primos_segundo_grau:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        filhos_dos_primos_segundo_grau.extend(filhos_do_primo)  # Adiciona à lista geral

    # Eliminar possíveis duplicatas baseado em ID (opcional, dependendo dos dados)
    unique_filhos = {f['ID']: f for f in filhos_dos_primos_segundo_grau}.values()

    return list(unique_filhos)


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_trisavos(df, pessoa_id):
    """Busca os trisavós de uma pessoa no DataFrame."""
    bisavos = buscar_bisavos(df, pessoa_id)  # Obtemos a lista de bisavós
    trisavos = []

    # Para cada bisavó, encontrar seus pais (os trisavós da pessoa original)
    for bisavo in bisavos:
        bisavo_id = bisavo['ID']
        pais_do_bisavo = buscar_pais(df, bisavo_id)  # Reutiliza a função buscar_pais para obter os pais do bisavó
        if pais_do_bisavo['pai']:  # Verifica se existe um registro para o avô paterno do bisavó
            avo_paterno_info = buscar_nome_sobrenome_por_id(df, pais_do_bisavo['pai'])
            trisavos.append({'ID': pais_do_bisavo['pai'], 'Nome Completo': avo_paterno_info})
        if pais_do_bisavo['mae']:  # Verifica se existe um registro para a avó materna do bisavó
            avo_materna_info = buscar_nome_sobrenome_por_id(df, pais_do_bisavo['mae'])
            trisavos.append({'ID': pais_do_bisavo['mae'], 'Nome Completo': avo_materna_info})

    # Eliminar possíveis duplicatas baseado em ID
    unique_trisavos = {trisavo['ID']: trisavo for trisavo in trisavos}.values()

    return list(unique_trisavos)


def buscar_tios_bisavos(df, pessoa_id):
    """Busca todos os tios-bisavôs e tias-bisavós de uma pessoa no DataFrame, que são os filhos dos trisavós, excluindo os próprios bisavós."""
    trisavos = buscar_trisavos(df, pessoa_id)  # Primeiro, encontrar todos os trisavós da pessoa
    bisavos = buscar_bisavos(df, pessoa_id)  # Encontrar todos os bisavós para evitar incluí-los
    bisavos_ids = set([bisavo['ID'] for bisavo in bisavos if bisavo['ID'] is not None])  # Cria um conjunto de IDs de bisavós
    tios_bisavos = []

    # Para cada trisavó encontrado, buscar seus filhos, excluindo os bisavós
    for trisavo in trisavos:
        trisavo_id = trisavo['ID']
        filhos_do_trisavo = buscar_filhos(df, trisavo_id)  # Busca filhos do trisavó
        for filho in filhos_do_trisavo:
            if filho['ID'] not in bisavos_ids:  # Verifica se o filho não é um dos bisavós
                tios_bisavos.append(filho)  # Adiciona à lista de tios-bisavós se não for um bisavó

    # Eliminar duplicatas baseado em ID, se necessário
    unique_tios_bisavos = {tio['ID']: tio for tio in tios_bisavos}.values()

    return list(unique_tios_bisavos)


def buscar_primos_primeiro_grau_dos_avos(df, pessoa_id):
    """Busca os primos de primeiro grau dos avós de uma pessoa, excluindo os próprios avós."""
    avos = buscar_avos(df, pessoa_id)  # Obtemos a lista de avós para evitar incluí-los
    avos_ids = {avo['ID'] for avo in avos if 'ID' in avo}  # Cria um conjunto de IDs dos avós
    tios_bisavos = buscar_tios_bisavos(df, pessoa_id)  # Obtemos a lista de tios-bisavós e tias-bisavós
    primos_dos_avos = []

    # Para cada tio-bisavô e tia-bisavó, buscar seus filhos
    for tio_bisavo in tios_bisavos:
        tio_bisavo_id = tio_bisavo['ID']
        filhos_do_tio_bisavo = buscar_filhos(df, tio_bisavo_id)  # Utiliza a função buscar_filhos para obter filhos
        # Adiciona à lista geral apenas se o filho não for um dos avós
        for filho in filhos_do_tio_bisavo:
            if filho['ID'] not in avos_ids:
                primos_dos_avos.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_dos_avos}.values()

    return list(unique_primos)


def buscar_primos_segundo_grau_dos_pais(df, pessoa_id):
    """Busca os primos de segundo grau do pai ou da mãe de uma pessoa, excluindo os próprios pais."""
    pais = buscar_pais(df, pessoa_id)  # Busca os pais para excluir seus IDs
    pais_ids = {pais['pai'], pais['mae']}  # Cria um conjunto com os IDs dos pais
    primos_primeiro_grau_dos_avos = buscar_primos_primeiro_grau_dos_avos(df, pessoa_id)
    primos_segundo_grau_dos_pais = []

    # Para cada primo de primeiro grau do avô/avó, buscar seus filhos
    for primo in primos_primeiro_grau_dos_avos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        # Adiciona à lista geral apenas se o filho não for um dos pais
        for filho in filhos_do_primo:
            if filho['ID'] not in pais_ids:
                primos_segundo_grau_dos_pais.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_segundo_grau_dos_pais}.values()

    return list(unique_primos)


def buscar_primos_terceiro_grau(df, pessoa_id):
    """Busca os primos de terceiro grau de uma pessoa, que são os filhos dos primos de segundo grau dos pais."""
    primos_segundo_grau_dos_pais = buscar_primos_segundo_grau_dos_pais(df, pessoa_id)  # Obtemos a lista de primos de segundo grau dos pais
    primos_terceiro_grau = []

    # Para cada primo de segundo grau do pai/da mãe, buscar seus filhos
    for primo in primos_segundo_grau_dos_pais:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        primos_terceiro_grau.extend(filhos_do_primo)  # Adiciona à lista geral

    # Eliminar possíveis duplicatas baseado em ID (opcional, dependendo dos dados)
    unique_primos = {primo['ID']: primo for primo in primos_terceiro_grau}.values()

    return list(unique_primos)


def buscar_filhos_dos_primos_terceiro_grau(df, pessoa_id):
    """Busca os filhos dos primos de terceiro grau de uma pessoa."""
    primos_terceiro_grau = buscar_primos_terceiro_grau(df, pessoa_id)  # Obtemos a lista de primos de terceiro grau
    filhos_dos_primos_terceiro_grau = []

    # Para cada primo de terceiro grau, buscar seus filhos
    for primo in primos_terceiro_grau:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        filhos_dos_primos_terceiro_grau.extend(filhos_do_primo)  # Adiciona à lista geral

    # Eliminar possíveis duplicatas baseado em ID
    unique_filhos = {filho['ID']: filho for filho in filhos_dos_primos_terceiro_grau}.values()

    return list(unique_filhos)


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_tetravos(df, pessoa_id):
    """Busca os tetravós de uma pessoa, que são os pais dos trisavós."""
    trisavos = buscar_trisavos(df, pessoa_id)  # Obtemos a lista de trisavós
    tetravos = []

    # Para cada trisavó, encontrar seus pais (os tetravós da pessoa original)
    for trisavo in trisavos:
        trisavo_id = trisavo['ID']
        pais_do_trisavo = buscar_pais(df, trisavo_id)  # Reutiliza a função buscar_pais para obter os pais do trisavó
        if pais_do_trisavo['pai']:  # Verifica se existe um registro para o avô paterno do trisavó
            avo_paterno_info = buscar_nome_sobrenome_por_id(df, pais_do_trisavo['pai'])
            tetravos.append({'ID': pais_do_trisavo['pai'], 'Nome Completo': avo_paterno_info})
        if pais_do_trisavo['mae']:  # Verifica se existe um registro para a avó materna do trisavó
            avo_materna_info = buscar_nome_sobrenome_por_id(df, pais_do_trisavo['mae'])
            tetravos.append({'ID': pais_do_trisavo['mae'], 'Nome Completo': avo_materna_info})

    # Eliminar possíveis duplicatas baseado em ID
    unique_tetravos = {tetravo['ID']: tetravo for tetravo in tetravos}.values()

    return list(unique_tetravos)


def buscar_tios_trisavos(df, pessoa_id):
    """Busca os tios-trisavôs e tias-trisavós de uma pessoa, que são os filhos dos tetravós, excluindo os próprios trisavós."""
    trisavos = buscar_trisavos(df, pessoa_id)  # Obtemos a lista de trisavós
    trisavos_ids = {trisavo['ID'] for trisavo in trisavos if trisavo['ID'] is not None}  # Conjunto de IDs dos trisavós
    tetravos = buscar_tetravos(df, pessoa_id)  # Obtemos a lista de tetravós
    tios_trisavos = []

    # Para cada tetravô, buscar seus filhos (tios-trisavôs e tias-trisavós), excluindo os trisavós
    for tetravo in tetravos:
        tetravo_id = tetravo['ID']
        filhos_do_tetravo = buscar_filhos(df, tetravo_id)  # Utiliza a função buscar_filhos para obter filhos
        for filho in filhos_do_tetravo:
            if filho['ID'] not in trisavos_ids:
                tios_trisavos.append(filho)

    # Eliminar duplicatas baseado em ID
    unique_tios_trisavos = {tio['ID']: tio for tio in tios_trisavos}.values()

    return list(unique_tios_trisavos)


def buscar_primos_primeiro_grau_dos_bisavos(df, pessoa_id):
    """Busca os primos de primeiro grau dos bisavós de uma pessoa, que são os filhos dos tios-trisavôs e tias-trisavós, excluindo os próprios bisavós."""
    bisavos = buscar_bisavos(df, pessoa_id)  # Obtemos a lista de bisavós para evitar incluí-los
    bisavos_ids = {bisavo['ID'] for bisavo in bisavos if 'ID' in bisavo}  # Cria um conjunto de IDs dos bisavós
    tios_trisavos = buscar_tios_trisavos(df, pessoa_id)  # Obtemos a lista de tios-trisavós e tias-trisavós
    primos_dos_bisavos = []

    # Para cada tio-trisavô e tia-trisavó, buscar seus filhos
    for tio_trisavo in tios_trisavos:
        tio_trisavo_id = tio_trisavo['ID']
        filhos_do_tio_trisavo = buscar_filhos(df, tio_trisavo_id)  # Utiliza a função buscar_filhos para obter filhos
        # Adiciona à lista geral apenas se o filho não for um dos bisavós
        for filho in filhos_do_tio_trisavo:
            if filho['ID'] not in bisavos_ids:
                primos_dos_bisavos.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_dos_bisavos}.values()

    return list(unique_primos)


def buscar_primos_segundo_grau_dos_avos(df, pessoa_id):
    """Busca os primos de segundo grau dos avós de uma pessoa, que são os filhos dos primos de primeiro grau dos bisavós, excluindo os próprios avós."""
    avos = buscar_avos(df, pessoa_id)  # Obtemos a lista de avós para evitar incluí-los
    avos_ids = {avo['ID'] for avo in avos if 'ID' in avo}  # Cria um conjunto de IDs dos avós
    primos_primeiro_grau_dos_bisavos = buscar_primos_primeiro_grau_dos_bisavos(df, pessoa_id)  # Lista de primos de 1º grau dos bisavós
    primos_segundo_grau_dos_avos = []

    # Para cada primo de primeiro grau dos bisavós, buscar seus filhos
    for primo in primos_primeiro_grau_dos_bisavos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        # Adiciona à lista geral apenas se o filho não for um dos avós
        for filho in filhos_do_primo:
            if filho['ID'] not in avos_ids:
                primos_segundo_grau_dos_avos.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_segundo_grau_dos_avos}.values()

    return list(unique_primos)


def buscar_primos_terceiro_grau_dos_pais(df, pessoa_id):
    """Busca os primos de terceiro grau do pai ou da mãe de uma pessoa, que são os filhos dos primos de segundo grau dos avós, excluindo os próprios pais."""
    pais = buscar_pais(df, pessoa_id)  # Busca os pais para excluir seus IDs
    pais_ids = {pais['pai'], pais['mae']}  # Cria um conjunto com os IDs dos pais
    primos_segundo_grau_dos_avos = buscar_primos_segundo_grau_dos_avos(df, pessoa_id)  # Lista de primos de 2º grau dos avós
    primos_terceiro_grau_dos_pais = []

    # Para cada primo de segundo grau dos avós, buscar seus filhos
    for primo in primos_segundo_grau_dos_avos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)  # Utiliza a função buscar_filhos para obter filhos
        # Adiciona à lista geral apenas se o filho não for um dos pais
        for filho in filhos_do_primo:
            if filho['ID'] not in pais_ids:
                primos_terceiro_grau_dos_pais.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_terceiro_grau_dos_pais}.values()

    return list(unique_primos)


def buscar_primos_quarto_grau(df, pessoa_id):
    """Busca os primos de quarto grau de uma pessoa, que são os filhos dos primos de terceiro grau do pai/da mãe."""
    primos_terceiro_grau_dos_pais = buscar_primos_terceiro_grau_dos_pais(df, pessoa_id)
    primos_quarto_grau = []

    for primo in primos_terceiro_grau_dos_pais:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        primos_quarto_grau.extend(filhos_do_primo)

    unique_primos = {primo['ID']: primo for primo in primos_quarto_grau}.values()
    return list(unique_primos)


def buscar_filhos_dos_primos_quarto_grau(df, pessoa_id):
    """Busca os filhos dos primos de quarto grau de uma pessoa."""
    primos_quarto_grau = buscar_primos_quarto_grau(df, pessoa_id)
    filhos_dos_primos_quarto_grau = []

    for primo in primos_quarto_grau:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        filhos_dos_primos_quarto_grau.extend(filhos_do_primo)

    unique_filhos = {filho['ID']: filho for filho in filhos_dos_primos_quarto_grau}.values()
    return list(unique_filhos)


# ---------------------------------------------------------------------------------------------------------------------------

def buscar_pentavos(df, pessoa_id):
    """Busca os pentavós de uma pessoa, que são os pais dos tetravós."""
    tetravos = buscar_tetravos(df, pessoa_id)
    pentavos = []

    for tetravo in tetravos:
        tetravo_id = tetravo['ID']
        pais_do_tetravo = buscar_pais(df, tetravo_id)
        pentavos.extend([{'ID': pai['pai'], 'Nome Completo': buscar_nome_sobrenome_por_id(df, pai['pai'])} for pai in [pais_do_tetravo] if pai['pai']])
        pentavos.extend([{'ID': pai['mae'], 'Nome Completo': buscar_nome_sobrenome_por_id(df, pai['mae'])} for pai in [pais_do_tetravo] if pai['mae']])

    unique_pentavos = {avo['ID']: avo for avo in pentavos if avo['ID']}.values()
    return list(unique_pentavos)


def buscar_tios_tetravos(df, pessoa_id):
    """Busca os tios-tetravôs e tias-tetravôs de uma pessoa, que são os filhos dos pentavós, excluindo os próprios tetravós."""
    pentavos = buscar_pentavos(df, pessoa_id)  # Obtemos a lista de pentavós
    tetravos = buscar_tetravos(df, pessoa_id)  # Obtemos a lista de tetravós para evitar incluí-los
    tetravos_ids = {tetravo['ID'] for tetravo in tetravos if tetravo['ID'] is not None}  # Conjunto de IDs dos tetravós
    tios_tetravos = []

    # Para cada pentavó, buscar seus filhos, excluindo os próprios tetravós
    for pentavo in pentavos:
        pentavo_id = pentavo['ID']
        filhos_do_pentavo = buscar_filhos(df, pentavo_id)
        # Adicionar à lista apenas se o ID do filho não for um dos tetravós
        for filho in filhos_do_pentavo:
            if filho['ID'] not in tetravos_ids:
                tios_tetravos.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_tios_tetravos = {tio['ID']: tio for tio in tios_tetravos}.values()

    return list(unique_tios_tetravos)


def buscar_primos_primeiro_grau_dos_trisavos(df, pessoa_id):
    """Busca os primos de primeiro grau dos trisavós de uma pessoa, que são os filhos dos tio-tetravôs e tia-tetravôs, excluindo os próprios trisavós."""
    trisavos = buscar_trisavos(df, pessoa_id)  # Primeiro, encontrar todos os trisavós da pessoa
    trisavos_ids = {trisavo['ID'] for trisavo in trisavos if trisavo['ID'] is not None}  # Conjunto de IDs dos trisavós
    tios_tetravos = buscar_tios_tetravos(df, pessoa_id)
    primos_trisavos = []

    for tio_tetravo in tios_tetravos:
        tio_tetravo_id = tio_tetravo['ID']
        filhos_do_tio_tetravo = buscar_filhos(df, tio_tetravo_id)
        # Adicionar à lista apenas se o ID do filho não for um dos trisavós
        for filho in filhos_do_tio_tetravo:
            if filho['ID'] not in trisavos_ids:
                primos_trisavos.append(filho)

    # Eliminar duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_trisavos}.values()
    return list(unique_primos)


def buscar_primos_segundo_grau_dos_bisavos(df, pessoa_id):
    """Busca os primos de segundo grau dos bisavós de uma pessoa, que são os filhos dos primos de primeiro grau dos trisavós, excluindo os próprios bisavós."""
    bisavos = buscar_bisavos(df, pessoa_id)  # Buscar os bisavós para excluir seus IDs
    bisavos_ids = {bisavo['ID'] for bisavo in bisavos if bisavo['ID'] is not None}  # Conjunto de IDs dos bisavós
    primos_primeiro_grau_dos_trisavos = buscar_primos_primeiro_grau_dos_trisavos(df, pessoa_id)
    primos_segundo_grau_dos_bisavos = []

    for primo_trisavo in primos_primeiro_grau_dos_trisavos:
        primo_trisavo_id = primo_trisavo['ID']
        filhos_do_primo_trisavo = buscar_filhos(df, primo_trisavo_id)
        # Adicionar à lista apenas se o ID do filho não for um dos bisavós
        for filho in filhos_do_primo_trisavo:
            if filho['ID'] not in bisavos_ids:
                primos_segundo_grau_dos_bisavos.append(filho)

    # Eliminar duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_segundo_grau_dos_bisavos}.values()
    return list(unique_primos)


def buscar_primos_terceiro_grau_dos_avos(df, pessoa_id):
    """Busca os primos de terceiro grau dos avós de uma pessoa, que são os filhos dos primos de segundo grau dos bisavós, excluindo os próprios avós."""
    avos = buscar_avos(df, pessoa_id)  # Obtemos a lista de avós para evitar incluí-los
    avos_ids = {avo['ID'] for avo in avos if avo and 'ID' in avo}  # Cria um conjunto de IDs dos avós, garantindo que 'ID' existe

    primos_segundo_grau_dos_bisavos = buscar_primos_segundo_grau_dos_bisavos(df, pessoa_id)
    primos_terceiro_grau_dos_avos = []

    for primo in primos_segundo_grau_dos_bisavos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        # Adicionar à lista apenas se o ID do filho não for um dos avós
        for filho in filhos_do_primo:
            if filho['ID'] not in avos_ids:
                primos_terceiro_grau_dos_avos.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_terceiro_grau_dos_avos}.values()
    return list(unique_primos)


def buscar_primos_quarto_grau_dos_pais(df, pessoa_id):
    """Busca os primos de quarto grau do pai ou da mãe de uma pessoa, que são os filhos dos primos de terceiro grau dos avós, excluindo os próprios pais."""
    pais = buscar_pais(df, pessoa_id)  # Busca os pais para excluir seus IDs
    pais_ids = {pais['pai'], pais['mae']}  # Cria um conjunto com os IDs dos pais
    primos_terceiro_grau_dos_avos = buscar_primos_terceiro_grau_dos_avos(df, pessoa_id)
    primos_quarto_grau_dos_pais = []

    for primo in primos_terceiro_grau_dos_avos:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        # Adicionar à lista apenas se o ID do filho não for um dos pais
        for filho in filhos_do_primo:
            if filho['ID'] not in pais_ids:
                primos_quarto_grau_dos_pais.append(filho)

    # Eliminar possíveis duplicatas baseado em ID
    unique_primos = {primo['ID']: primo for primo in primos_quarto_grau_dos_pais}.values()
    return list(unique_primos)


def buscar_primos_quinto_grau(df, pessoa_id):
    """Busca os primos de quinto grau de uma pessoa, que são os filhos dos primos de quarto grau do pai ou da mãe."""
    primos_quarto_grau_dos_pais = buscar_primos_quarto_grau_dos_pais(df, pessoa_id)
    primos_quinto_grau = []

    for primo in primos_quarto_grau_dos_pais:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        primos_quinto_grau.extend(filhos_do_primo)

    unique_primos = {primo['ID']: primo for primo in primos_quinto_grau}.values()
    return list(unique_primos)


def buscar_filhos_dos_primos_quinto_grau(df, pessoa_id):
    """Busca os filhos dos primos de quinto grau de uma pessoa."""
    primos_quinto_grau = buscar_primos_quinto_grau(df, pessoa_id)
    filhos_dos_primos_quinto_grau = []

    for primo in primos_quinto_grau:
        primo_id = primo['ID']
        filhos_do_primo = buscar_filhos(df, primo_id)
        filhos_dos_primos_quinto_grau.extend(filhos_do_primo)

    unique_filhos = {filho['ID']: filho for filho in filhos_dos_primos_quinto_grau}.values()
    return list(unique_filhos)

# ------------------------------------------------------------------------------------------------------------------------------------------

def imprimir_familia_extensa(df, pessoa_id):
    nome_completo = buscar_nome_sobrenome_por_id(df, pessoa_id)
    
    # Pais
    pais_ids = buscar_pais(df, pessoa_id)
    pais = []
    if pais_ids['pai']:
        pai_info = buscar_nome_sobrenome_por_id(df, pais_ids['pai'])
        pais.append({'ID': pais_ids['pai'], 'Nome Completo': pai_info})
    if pais_ids['mae']:
        mae_info = buscar_nome_sobrenome_por_id(df, pais_ids['mae'])
        pais.append({'ID': pais_ids['mae'], 'Nome Completo': mae_info})

    imprimir_parentes(df, pessoa_id, pais, "Pais")
    
    # Filhos
    filhos = buscar_filhos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos, "Filhos")

    # Irmãos
    irmaos = buscar_irmaos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, irmaos, "Irmãos")
    
    # Sobrinhos
    sobrinhos = buscar_sobrinhos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, sobrinhos, "Sobrinhos")
    
    # Avós
    avos = buscar_avos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, avos, "Avós")
    
    # Tios
    tios = buscar_tios(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tios, "Tios")
    
   # Primos de primeiro grau
    primos_primeiro_grau = buscar_primos_primeiro_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_primeiro_grau, "Primos de Primeiro Grau")
    
     # Filhos dos primos de primeiro grau
    filhos_dos_primos = buscar_filhos_dos_primos_primeiro_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos_dos_primos, "Filhos dos Primos de 1º Grau")
    
    # Bisavós
    bisavos = buscar_bisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, bisavos, "Bisavós")
    
    # Tios-avós
    tios_avos = buscar_tios_avos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tios_avos, "Tios-avós")
    
    # Primo(a) de 1º grau do pai/da mãe
    primos_primeiro_grau_pais = buscar_primos_primeiro_grau_dos_pais(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_primeiro_grau_pais, "Primo(a) de 1º Grau do pai/da mãe")
    
    # Primo(a) de 2º grau
    primos_segundo_grau = buscar_primos_segundo_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_segundo_grau, "Primo(a) de 2º Grau")
    
    # Filho(a) do(a) primo(a) de 2º grau
    filhos_primos_segundo_grau = buscar_filhos_dos_primos_segundo_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos_primos_segundo_grau, "Filho(a) do(a) primo(a) de 2º grau")
    
    # Trisavós
    trisavos = buscar_trisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, trisavos, "Trisavós")
    
    # Tio-bisavô/tia-bisavó
    tios_bisavos = buscar_tios_bisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tios_bisavos, "Tio-bisavô/tia-bisavó")
    
    # Primo(a) de 1º grau do avô/da avó
    primos_primeiro_grau_avos = buscar_primos_primeiro_grau_dos_avos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_primeiro_grau_avos, "Primo(a) de 1º grau do avô/da avó")
    
    # Primo(a) de 2º grau do pai/da mãe
    primos_segundo_grau_pais = buscar_primos_segundo_grau_dos_pais(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_segundo_grau_pais, "Primo(a) de 2º grau do pai/da mãe")
    
    # Primo(a) de 3º grau
    primos_terceiro_grau = buscar_primos_terceiro_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_terceiro_grau, "Primo(a) de 3º grau")
    
    # Filho(a) do(a) primo(a) de 3º grau
    filhos_primos_terceiro_grau = buscar_filhos_dos_primos_terceiro_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos_primos_terceiro_grau, "Filho(a) do(a) primo(a) de 3º grau")
    
    # Tetravós
    tetravos = buscar_tetravos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tetravos, "Tetravós")
    
    # Tio-trisavô/Tia-trisavó
    tios_trisavos = buscar_tios_trisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tios_trisavos, "Tio-trisavô/Tia-trisavó")
    
    # Primo(a) de 1º grau do bisavô/da bisavó
    primos_primeiro_grau_bisavos = buscar_primos_primeiro_grau_dos_bisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_primeiro_grau_bisavos, "Primo(a) de 1º grau do bisavô/da bisavó")
    
    # Primo(a) de 2º grau do avô/da avó
    primos_segundo_grau_avos = buscar_primos_segundo_grau_dos_avos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_segundo_grau_avos, "Primo(a) de 2º grau do avô/da avó")
    
    # Primo(a) de 3º grau do pai/da mãe
    primos_terceiro_grau_pais = buscar_primos_terceiro_grau_dos_pais(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_terceiro_grau_pais, "Primo(a) de 3º grau do pai/da mãe")
    
    # Primos de 4º Grau
    primos_quarto_grau = buscar_primos_quarto_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_quarto_grau, "Primos de 4º Grau")
    
    # Filhos dos Primos de 4º Grau
    filhos_primos_quarto_grau = buscar_filhos_dos_primos_quarto_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos_primos_quarto_grau, "Filhos dos Primos de 4º Grau")
    
    # Pentavós
    pentavos = buscar_pentavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, pentavos, "Pentavós")
    
    # Tio-tetravô/Tia-tetravó
    tios_tetravos = buscar_tios_tetravos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, tios_tetravos, "Tio-tetravô/Tia-tetravó")
    
    # Primos de 1º Grau do Trisavô/da Trisavó
    primos_primeiro_grau_trisavos = buscar_primos_primeiro_grau_dos_trisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_primeiro_grau_trisavos, "Primos de 1º Grau do Trisavô/da Trisavó")
    
    # Primos de 2º Grau do Bisavô/da Bisavó
    primos_segundo_grau_bisavos = buscar_primos_segundo_grau_dos_bisavos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_segundo_grau_bisavos, "Primos de 2º Grau do Bisavô/da Bisavó")
    
    # Primos de 3º Grau do Avô/da Avó
    primos_terceiro_grau_avos = buscar_primos_terceiro_grau_dos_avos(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_terceiro_grau_avos, "Primos de 3º Grau do Avô/da Avó")
    
    # Primos de 4º Grau do Pai/da Mãe
    primos_quarto_grau_pais = buscar_primos_quarto_grau_dos_pais(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_quarto_grau_pais, "Primos de 4º Grau do Pai/da Mãe")
    
    # Primos de 5º Grau
    primos_quinto_grau = buscar_primos_quinto_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, primos_quinto_grau, "Primos de 5º Grau")
    
    # Filhos dos Primos de 5º Grau
    filhos_primos_quinto_grau = buscar_filhos_dos_primos_quinto_grau(df, pessoa_id)
    imprimir_parentes(df, pessoa_id, filhos_primos_quinto_grau, "Filhos dos Primos de 5º Grau")   
    
# ------------------------------------------------------------------------------------------------------------------------------------------    

def imprimir_parentes(df, pessoa_id, parentes, parentesco):
    """Imprime os nomes dos parentes baseado nos dicionários fornecidos."""
    nome_completo = buscar_nome_sobrenome_por_id(df, pessoa_id)
    print(f"\n{parentesco} de {nome_completo}:")

    if isinstance(parentes, dict):
        # Verifica se é um dicionário de listas ou dicionário de IDs
        if all(isinstance(val, list) for val in parentes.values()):  # Se todos os valores são listas
            for categoria, lista_parentes in parentes.items():
                print(f"\n{categoria.capitalize()}:")
                if lista_parentes:
                    for parente in lista_parentes:
                        id_int = parente.get('ID')
                        nome_parente = buscar_nome_sobrenome_por_id(df, id_int) if id_int else "Desconhecido"
                        print(f"  ID: {id_int}, Nome: {nome_parente}")
                else:
                    print("  Nenhum encontrado")
        else:
            # Trata dicionários onde os valores são IDs diretamente (como para avós)
            for categoria, id_int in parentes.items():
                if id_int and id_int in df.index:
                    nome_parente = buscar_nome_sobrenome_por_id(df, id_int)
                    print(f"  {categoria}: ID {id_int}, Nome: {nome_parente}")
                else:
                    print(f"  {categoria}: Nenhum encontrado")
    elif parentes:  # Trata o caso onde 'parentes' é uma lista de dicionários
        for parente in parentes:
            id_int = parente.get('ID')
            nome_parente = buscar_nome_sobrenome_por_id(df, id_int) if id_int else "Desconhecido"
            print(f"  ID: {id_int}, Nome: {nome_parente}")
    else:
        print("  Nenhum parente encontrado na categoria.")

# ------------------------------------------------------------------------------------------------------------------------------------------

def encontrar_parentesco_direto(df, id1, id2):
    # Função auxiliar para criar o dicionário de parentesco
    def criar_dicionario_parentesco(id):
         return {
            'Pai/Mãe': buscar_pais(df, id),
            'filho(a)': buscar_filhos(df, id),
            'irmão(a)': buscar_irmaos(df, id),
            'sobrinho(a)': buscar_sobrinhos(df, id),
            'avô(ó)': buscar_avos(df, id),  # Assume-se que esta função retorna um dicionário
            'tio(a)': buscar_tios(df, id),
            'primo(a) 1º Grau': buscar_primos_primeiro_grau(df, id),
            'filho(a) do(a) primo(a) de 1º grau': buscar_filhos_dos_primos_primeiro_grau(df, id),
            'bisavo(a)': list(buscar_bisavos(df, id)),
            'Tio-Avô/Tia-Avó': buscar_tios_avos(df, id),
            'Primos de 1º Grau dos Pais': buscar_primos_primeiro_grau_dos_pais(df, id),
            'Primos de 2º Grau': buscar_primos_segundo_grau(df, id),
            'Filhos dos Primos de 2º Grau': buscar_filhos_dos_primos_segundo_grau(df, id),
            'Trisavós': list(buscar_trisavos(df, id)),
            'Tio-bisavô/tia-bisavó': list(buscar_tios_bisavos(df, id)),
            'Primos de 1º Grau do Avô/da Avó': buscar_primos_primeiro_grau_dos_avos(df, id),
            'Primos de 2º Grau do Pai/da Mãe': buscar_primos_segundo_grau_dos_pais(df, id),
            'Primos de 3º Grau': buscar_primos_terceiro_grau(df, id),
            'Filhos dos Primos de 3º Grau': buscar_filhos_dos_primos_terceiro_grau(df, id),
            'Tetravós': list(buscar_tetravos(df, id)),
            'Tio-trisavô/Tia-trisavó': list(buscar_tios_trisavos(df, id)),
            'Primos de 1º Grau do Bisavô/da Bisavó': buscar_primos_primeiro_grau_dos_bisavos(df, id),
            'Primos de 2º Grau do Avô/da Avó': buscar_primos_segundo_grau_dos_avos(df, id),
            'Primos de 3º Grau do Pai/da Mãe': buscar_primos_terceiro_grau_dos_pais(df, id),
            'Primos de 4º Grau': buscar_primos_quarto_grau(df, id),
            'Filhos dos Primos de 4º Grau': buscar_filhos_dos_primos_quarto_grau(df, id),
            'Pentavós': list(buscar_pentavos(df, id)),
            'Tio-tetravô/Tia-tetravó': list(buscar_tios_tetravos(df, id)),
            'Primos de 1º Grau do Trisavô/da Trisavó': buscar_primos_primeiro_grau_dos_trisavos(df, id),
            'Primos de 2º Grau do Bisavô/da Bisavó': buscar_primos_segundo_grau_dos_bisavos(df, id),
            'Primos de 3º Grau do Avô/da Avó': buscar_primos_terceiro_grau_dos_avos(df, id),
            'Primos de 4º Grau do Pai/da Mãe': buscar_primos_quarto_grau_dos_pais(df, id),
            'Primos de 5º Grau': buscar_primos_quinto_grau(df, id),
            'Filhos dos Primos de 5º Grau': buscar_filhos_dos_primos_quinto_grau(df, id)
        }
    
    # Criar dicionários de parentesco para ambos os IDs
    parentescos_id1 = criar_dicionario_parentesco(id1)
    parentescos_id2 = criar_dicionario_parentesco(id2)

    return parentescos_id1, parentescos_id2

# ------------------------------------------------------------------------------------------------------------------------------------------

# Definindo a função que busca identificar o parentesco específico entre os IDs
def buscar_id_no_dicionario(dicionario, id_procurado):
    for chave, valor in dicionario.items():
        if isinstance(valor, dict):  # Verifica se o valor é um dicionário
            for subkey, subval in valor.items():
                if subval == id_procurado:
                    return chave + " -> " + subkey
        elif isinstance(valor, list):  # Verifica se é uma lista de dicionários
            for item in valor:
                if item.get('ID') == id_procurado:
                    return chave
    return None

# ------------------------------------------------------------------------------------------------------------------------------------------

# def coletar_todos_antepassados(df, pessoa_id, atual_geracao=0, antepassados=None, visitados=None):
#     """
#     Coleta todos os antepassados de uma pessoa com base no ID fornecido.
#     Evita loops causados por ciclos na árvore genealógica.
#     """
#     if antepassados is None:
#         antepassados = {}
#     if visitados is None:
#         visitados = set()

#     # Se a pessoa já foi visitada, retorna para evitar ciclos
#     if pessoa_id in visitados:
#         return antepassados

#     # Marca a pessoa como visitada
#     visitados.add(pessoa_id)

#     try:
#         # Obter IDs dos pais
#         pai_id = df.at[pessoa_id, 'Pai_ID'] if 'Pai_ID' in df.columns and pd.notna(df.at[pessoa_id, 'Pai_ID']) else None
#         mae_id = df.at[pessoa_id, 'Mae_ID'] if 'Mae_ID' in df.columns and pd.notna(df.at[pessoa_id, 'Mae_ID']) else None

#         # Adiciona os pais como antepassados
#         if pai_id is not None:
#             antepassados[pai_id] = atual_geracao + 1
#             coletar_todos_antepassados(df, pai_id, atual_geracao + 1, antepassados, visitados)
#         if mae_id is not None:
#             antepassados[mae_id] = atual_geracao + 1
#             coletar_todos_antepassados(df, mae_id, atual_geracao + 1, antepassados, visitados)
#     except KeyError:
#         # Ignora erros se a pessoa não tiver 'Pai_ID' ou 'Mae_ID' válidos
#         pass

#     return antepassados

def coletar_todos_antepassados(df, pessoa_id, atual_geracao=1, antepassados=None):
    if antepassados is None:
        antepassados = {}

    # Busca os pais da pessoa
    pais = buscar_pais(df, pessoa_id)
    for pai in pais.values():
        # Verifica se 'pai' é um inteiro e maior que zero
        if pai is not None and pai > 0:  # Ignora IDs inválidos e None
            antepassados[pai] = atual_geracao
            # Recursivamente busca os antepassados do pai/mãe
            coletar_todos_antepassados(df, pai, atual_geracao + 1, antepassados)

    return antepassados

# ----------------------------------------------------------------------------------------------------------------------------------------

def geracao_para_termo(geracao):
    # Mapeia o número de geração para o termo de parentesco correspondente
    termos = {
        1: "Pais",
        2: "Avós",
        3: "Bisavós",
        4: "Trisavós",
        5: "Tetravós",
        6: "Pentavós",
        # Adicione mais conforme necessário
    }
    return termos.get(geracao, f"Antepassado de {geracao}ª geração")

# -------------------------------------------------------------------------------------------------------------------------------------

def exibir_antepassados_comuns_e_parentesco(df, id1, id2):
    antepassados_id1 = coletar_todos_antepassados(df, id1)
    antepassados_id2 = coletar_todos_antepassados(df, id2)

    # Encontrando antepassados comuns e suas gerações
    antepassados_comuns = {antepassado: (antepassados_id1[antepassado], antepassados_id2[antepassado])
                           for antepassado in set(antepassados_id1) & set(antepassados_id2)}
    
    # Ordenando antepassados comuns pela soma das gerações para os dois IDs
    antepassados_ordenados = sorted(antepassados_comuns.items(), key=lambda x: x[1][0] + x[1][1])
    
     
    for antepassado, (grau_id1, grau_id2) in antepassados_ordenados:
        nome_antepassado = buscar_nome_sobrenome_por_id(df, antepassado)        
        print(f"- {nome_antepassado}:")
        print(f"  {geracao_para_termo(grau_id1)} de {buscar_nome_sobrenome_por_id(df, id1)}")
        print(f"  {geracao_para_termo(grau_id2)} de {buscar_nome_sobrenome_por_id(df, id2)}")
        print('')

# ------------------------------------------------------------------------------------------------------------------------------------------

def buscar_por_nome_ou_sobrenome(df, texto_procurado, colunas_selecionadas):
    """
    Filtra o DataFrame para encontrar linhas onde o nome completo ou identificador contenha o texto procurado,
    ou onde o ID seja exatamente igual ao valor digitado.
    A busca é case-insensitive para nomes e identificadores, mas exata para IDs.
    Retorna apenas as colunas selecionadas.
    """
    if texto_procurado.strip():  # Verifica se o texto procurado não está vazio
        texto_procurado = texto_procurado.strip()  # Remove espaços extras
        
        # Garantir que as colunas necessárias estão disponíveis
        colunas_existentes = df.columns
        filtros = []

        # Busca parcial para Nome Completo
        if 'Nome Completo' in colunas_existentes:
            filtros.append(df['Nome Completo'].str.contains(texto_procurado, case=False, na=False))
        
        # Busca parcial para Identificador
        if 'Identificador' in colunas_existentes:
            filtros.append(df['Identificador'].str.contains(texto_procurado, case=False, na=False))
        
        # Busca exata para ID
        if texto_procurado.isdigit():  # Verifica se o texto é numérico
            filtros.append(df.index == int(texto_procurado))  # Comparação exata com o índice
        
        if filtros:  # Se houver pelo menos uma condição
            resultados = filtros.pop()  # Inicia com o primeiro filtro
            for filtro in filtros:
                resultados |= filtro  # Combina filtros com OR

            # Retorna apenas as colunas selecionadas, se forem válidas
            if colunas_selecionadas:
                colunas_validas = [col for col in colunas_selecionadas if col in colunas_existentes]
                return df.loc[resultados, colunas_validas]
            else:
                return df[resultados]  # Retorna todas as colunas, se nenhuma foi selecionada
        
    return pd.DataFrame(columns=colunas_selecionadas)  # Retorna um DataFrame vazio com as colunas selecionadas

# -----------------------------------------------------------------------------------------------------------------------------

def wrap_text(text, width, font_size, pdf_canvas):
    """
    Quebra o texto em linhas com base na largura especificada.
    """
    lines = simpleSplit(text, pdf_canvas._fontname, font_size, width)
    return lines


def exibir_antepassados_comuns_ordenados_pdf(df, id_referencia, ids_lista, retornar_texto=False):
    """
    Exibe apenas o primeiro ancestral comum mais próximo entre o ID de referência e os IDs fornecidos,
    agrupando os descendentes por ancestral comum.
    Salva em PDF e retorna o texto (opcional).
    """
    nome_referencia = buscar_nome_sobrenome_por_id(df, id_referencia)
    output_pdf = f"Relatorio_{nome_referencia}.pdf"

    pdf = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    text_y_position = height - 40
    max_line_width = width - 80

    ancestrais_agrupados = defaultdict(list)
    texto_relatorio = f"Relatório de Ancestrais Comuns para: {nome_referencia} (ID: {id_referencia})\n\n"

    # Processar IDs de comparação
    for pessoa_id in ids_lista:
        antepassados_referencia = coletar_todos_antepassados(df, id_referencia)
        antepassados_pessoa = coletar_todos_antepassados(df, pessoa_id)

        ancestral_comum_mais_proximo = None
        menor_grau_referencia = float('inf')
        menor_grau_pessoa = float('inf')

        for ancestral_id in antepassados_referencia.keys() & antepassados_pessoa.keys():
            grau_referencia = antepassados_referencia[ancestral_id]
            grau_pessoa = antepassados_pessoa[ancestral_id]
            if grau_referencia < menor_grau_referencia or (
                grau_referencia == menor_grau_referencia and grau_pessoa < menor_grau_pessoa
            ):
                ancestral_comum_mais_proximo = ancestral_id
                menor_grau_referencia = grau_referencia
                menor_grau_pessoa = grau_pessoa

        if ancestral_comum_mais_proximo:
            nome_ancestral = buscar_nome_sobrenome_por_id(df, ancestral_comum_mais_proximo)
            grau_referencia_str = geracao_para_termo(menor_grau_referencia)
            grau_pessoa_str = geracao_para_termo(menor_grau_pessoa)

            # Agrupar por ancestral comum
            ancestrais_agrupados[(ancestral_comum_mais_proximo, nome_ancestral, grau_referencia_str)].append(
                {
                    "ID": pessoa_id,
                    "Nome": buscar_nome_sobrenome_por_id(df, pessoa_id),
                    "Grau": grau_pessoa_str,
                }
            )

    # Gerar relatório consolidado
    pdf.setFont("Helvetica", 10)
    for (ancestral_id, nome_ancestral, grau_ancestral), descendentes in ancestrais_agrupados.items():
        texto_relatorio += f"Ancestral Comum: {nome_ancestral} (ID: {ancestral_id}, Grau: {grau_ancestral})\n"
        pdf.drawString(40, text_y_position, f"Ancestral Comum: {nome_ancestral} (ID: {ancestral_id}, Grau: {grau_ancestral})")
        text_y_position -= 15

        for desc in descendentes:
            texto_relatorio += f"  - ID Comparado: {desc['ID']}, Nome: {desc['Nome']}, Grau: {desc['Grau']}\n"
            line = f"  - ID Comparado: {desc['ID']}, Nome: {desc['Nome']}, Grau: {desc['Grau']}"
            if text_y_position < 40:  # Verificar espaço na página
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                text_y_position = height - 40
            pdf.drawString(60, text_y_position, line)
            text_y_position -= 15

        texto_relatorio += "\n"
        text_y_position -= 10  # Espaço entre ancestrais

    if not ancestrais_agrupados:
        texto_relatorio += "Nenhum ancestral comum encontrado para os IDs fornecidos.\n"
        pdf.drawString(40, text_y_position, "Nenhum ancestral comum encontrado para os IDs fornecidos.")

    pdf.save()

    if retornar_texto:
        return output_pdf, texto_relatorio  # Retorna o caminho do PDF e o texto

    return output_pdf


def criar_relatorios_para_ids(df, ids_referencia, ids_lista):
    """
    Gera relatórios em PDF para cada ID de referência fornecido, comparando com a lista de IDs.
    Compacta os arquivos gerados em um único arquivo zip.
    """
    pdf_files = []
    for id_referencia in ids_referencia:
        print(f"Gerando relatório para ID de referência: {id_referencia}...")
        pdf_file = exibir_antepassados_comuns_ordenados_pdf(df, id_referencia, ids_lista)
        pdf_files.append(pdf_file)
        print(f"Relatório para ID {id_referencia} gerado com sucesso!")

    # Compactar todos os arquivos PDF em um único arquivo zip
    zip_file_name = "Relatorios_Ancestrais.zip"
    with zipfile.ZipFile(zip_file_name, 'w') as zipf:
        for pdf in pdf_files:
            zipf.write(pdf)
            os.remove(pdf)  # Opcional: remove o arquivo PDF após compactar

    print(f"Arquivos compactados em: {zip_file_name}")

# Exemplo de uso:
ids_referencia = [8166, 8150, 8122, 8072, 8065, 8050, 8028, 8008, 7977, 7968, 7937, 7953, 7883, 7800, 7732, 7676, 7642, 180, 7574, 7565, 7514, 7469, 7466, 7443, 7414, 7409, 7397, 7387,
                  7334, 5430, 7298, 7245, 7199, 7190, 7159, 7122, 7050, 7051, 2920, 100, 6236, 6207,
                  5970, 874, 3544, 3545, 6960, 5800, 5588, 934, 712, 6483, 5856, 6778, 2868, 996, 997,
                  5244, 6170, 5471, 535, 2132, 6023, 657, 5151, 5879, 1994, 6106, 5963, 2526, 5305,
                  6534, 5229, 548, 6139, 4333, 6219, 7040, 6656, 6237, 6984, 6861, 6911, 1500, 6848]  # Lista de IDs de referência para os quais os relatórios serão gerados

ids_lista = [8166, 8150, 8122, 8072, 8065, 8050, 8028, 8008, 7977, 7968, 7937, 7953, 7883, 7800, 7732, 7676,
             7642, 180, 7574, 7565, 7514, 7469, 7466, 7443, 7414, 7409, 7397, 7387,
             7334, 5430, 7298, 7245, 7199, 7190, 7159, 7122, 7050, 7051, 2920, 100, 6236, 6207,
             5970, 874, 3544, 3545, 6960, 5800, 5588, 934, 712, 6483, 5856, 6778, 2868, 996, 997,
             5244, 6170, 5471, 535, 2132, 6023, 657, 5151, 5879, 1994, 6106, 5963, 2526, 5305,
             6534, 5229, 548, 6139, 4333, 6219, 7040, 6656, 6237, 6984, 6861, 6911, 1500, 6848]  # Lista de IDs para comparação



# ---------------------------------------------------------------------------------------------------------

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from collections import defaultdict

def wrap_text(text, width, font_size, pdf_canvas):
    """
    Quebra o texto em linhas com base na largura especificada.
    """
    lines = simpleSplit(text, pdf_canvas._fontname, font_size, width)
    return lines


# ------------------------------------------------------------------------------------------

def obter_id_por_metodo(metodo_busca, termo_busca, familia_df, st):
    """
    Busca o ID baseado no método selecionado e no termo de busca.
    """
    if metodo_busca == "ID":
        return int(termo_busca)
    elif metodo_busca == "Identificador":
        filtro = familia_df["Identificador"] == termo_busca
        if filtro.any():
            return familia_df[filtro].index[0]
        else:
            st.warning(f"Nenhuma correspondência encontrada para o Identificador '{termo_busca}'.")
            st.stop()
    elif metodo_busca == "Nome Completo":
        filtro = familia_df["Nome Completo"].str.contains(termo_busca, case=False, na=False)
        if filtro.any():
            return familia_df[filtro].index[0]
        else:
            st.warning(f"Nenhuma correspondência encontrada para o Nome Completo '{termo_busca}'.")
            st.stop()

# ------------------------------------------------------------------------------------------------------------------------------

def exibir_antepassados_comuns_ordenados_pdf(df, id_referencia, ids_lista, retornar_texto=False, output_buffer=None):
    """
    Gera relatório de ancestrais comuns em PDF e retorna o texto formatado.
    """
    nome_referencia = df.loc[id_referencia, "Nome Completo"] if "Nome Completo" in df.columns else "Desconhecido"
    identificador_referencia = df.loc[id_referencia, "Identificador"] if "Identificador" in df.columns else "Desconhecido"
    output_pdf = f"Relatorio_Ancestrais_Comuns_{nome_referencia.replace(' ', '_')}.pdf"

    # Ajuste: Usar buffer se output_buffer for fornecido
    if output_buffer:
        pdf = canvas.Canvas(output_buffer, pagesize=A4)
    else:
        pdf = canvas.Canvas(output_pdf, pagesize=A4)

    width, height = A4
    text_y_position = height - 40
    max_line_width = width - 80

    # Título do relatório
    pdf.setFont("Helvetica-Bold", 14)
    titulo = f"Relatório de Ancestrais Comuns para:\n"
    titulo += f"{nome_referencia} (ID: {id_referencia}, Identificador: {identificador_referencia})"
    lines = wrap_text(titulo, max_line_width, 14, pdf)
    for line in lines:
        pdf.drawString(40, text_y_position, line)
        text_y_position -= 20

    text_y_position -= 20  # Espaço após o título

    ancestrais_agrupados = defaultdict(list)

    # Coletar antepassados do ID de referência
    antepassados_referencia = coletar_todos_antepassados(df, id_referencia)

    # Processar cada ID na lista
    for pessoa_id in ids_lista:
        antepassados_pessoa = coletar_todos_antepassados(df, pessoa_id)

        ancestral_comum_mais_proximo = None
        menor_grau_referencia = float('inf')
        menor_grau_pessoa = float('inf')

        for ancestral_id in antepassados_referencia.keys() & antepassados_pessoa.keys():
            grau_referencia = antepassados_referencia[ancestral_id]
            grau_pessoa = antepassados_pessoa[ancestral_id]

            if (grau_referencia < menor_grau_referencia) or \
               (grau_referencia == menor_grau_referencia and grau_pessoa < menor_grau_pessoa):
                ancestral_comum_mais_proximo = ancestral_id
                menor_grau_referencia = grau_referencia
                menor_grau_pessoa = grau_pessoa

        if ancestral_comum_mais_proximo:
            nome_ancestral = buscar_nome_sobrenome_por_id(df, ancestral_comum_mais_proximo)
            identificador_ancestral = df.at[ancestral_comum_mais_proximo, 'Identificador'] if 'Identificador' in df.columns else "Desconhecido"
            ancestrais_agrupados[(ancestral_comum_mais_proximo, nome_ancestral, identificador_ancestral)].append({
                'ID': pessoa_id,
                'Nome': buscar_nome_sobrenome_por_id(df, pessoa_id),
                'Grau': geracao_para_termo(menor_grau_pessoa)
            })

    pdf.setFont("Helvetica", 10)
    for (ancestral_id, nome_ancestral, identificador_ancestral), descendentes in ancestrais_agrupados.items():
        # Título do ancestral comum
        pdf.setFont("Helvetica-Bold", 12)
        texto_ancestral = f"Ancestral Comum: {nome_ancestral} (ID: {ancestral_id}, Identificador: {identificador_ancestral})"
        lines = wrap_text(texto_ancestral, max_line_width, 12, pdf)
        for line in lines:
            pdf.drawString(40, text_y_position, line)
            text_y_position -= 15

        # Grau de parentesco com a referência
        grau_referencia = antepassados_referencia.get(ancestral_id, None)
        if grau_referencia is not None:
            grau_referencia_texto = geracao_para_termo(grau_referencia)
            pdf.setFont("Helvetica-Oblique", 10)
            pdf.drawString(40, text_y_position, f"Grau de parentesco com a referência: {grau_referencia_texto}")
            text_y_position -= 15

        pdf.setFont("Helvetica", 10)

        # Definir larguras fixas para colunas
        col_id_x = 40          # Posição inicial da coluna ID
        col_identificador_x = 100  # Posição inicial da coluna Identificador
        col_nome_x = 200       # Posição inicial da coluna Nome
        col_grau_x = 430       # Posição inicial da coluna Grau
        col_spacing = 15       # Espaçamento vertical entre linhas

        for desc in descendentes:
            identificador = df.at[desc['ID'], 'Identificador'] if 'Identificador' in df.columns else "Desconhecido"
            pdf.drawString(col_id_x, text_y_position, f"{desc['ID']}")
            pdf.drawString(col_identificador_x, text_y_position, f"{identificador}")
            pdf.drawString(col_nome_x, text_y_position, f"{desc['Nome']}")
            pdf.drawString(col_grau_x, text_y_position, f"{desc['Grau']}")
            text_y_position -= col_spacing

            if text_y_position < 40:  # Criar uma nova página se necessário
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                text_y_position = height - 40

        text_y_position -= 20  # Espaço após cada ancestral

    if not ancestrais_agrupados:
        pdf.drawString(40, text_y_position, "Nenhum ancestral comum encontrado para os IDs fornecidos.")

    pdf.save()

    if retornar_texto:
        # Retornar o texto formatado para exibição no Streamlit
        texto_relatorio = f"Relatório de Ancestrais Comuns para:\n"  # Adicionada quebra de linha após os dois pontos
        texto_relatorio += f"{nome_referencia} ( ID: {id_referencia} | Identificador: {identificador_referencia} )\n\n"

        for (ancestral_id, nome_ancestral, identificador_ancestral), descendentes in ancestrais_agrupados.items():
            texto_relatorio += f"Ancestral Comum: {nome_ancestral} ( ID: {ancestral_id} | Identificador: {identificador_ancestral} )\n"
            grau_referencia = antepassados_referencia.get(ancestral_id, None)
            if grau_referencia is not None:
                grau_referencia_texto = geracao_para_termo(grau_referencia)
                texto_relatorio += f"Grau de parentesco com a referência: {grau_referencia_texto}\n"
            for desc in descendentes:
                texto_relatorio += f"{desc['ID']}, {desc['Nome']}, {desc['Grau']}\n"
            texto_relatorio += "\n"
        return output_pdf if not output_buffer else None, texto_relatorio

    return output_pdf if not output_buffer else None
