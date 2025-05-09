import pandas as pd
import sqlite3
import os


def inserir_no_banco(planilha):
    conn = sqlite3.connect('survey.db')
    cursor = conn.cursor()

    for index, row in planilha.iterrows():
        # Garantir formato de data
        data_nascimento = row['data_de_nascimento']
        if isinstance(data_nascimento, pd.Timestamp):
            data_nascimento = data_nascimento.strftime('%Y-%m-%d')

        # Limpar CPF: manter só os números
        cpf = ''.join(filter(str.isdigit, str(row['cpf'])))

        # Inserir no banco
        cursor.execute('''
            INSERT INTO colaboradores (nome, cpf, data_nascimento, funcao_inicial)
            VALUES (?, ?, ?, ?)
        ''', (row['nome'], cpf, data_nascimento, row['funcao_inicial']))

    conn.commit()
    conn.close()
    print("Dados inseridos com sucesso!")


def importar_planilha(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return

    # Carregar planilha
    planilha = pd.read_excel(caminho_arquivo)

    # Normalizar nomes das colunas
    planilha.columns = [col.strip().lower().replace(" ", "_") for col in planilha.columns]

    # Converter datas
    if 'data_de_nascimento' in planilha.columns:
        planilha['data_de_nascimento'] = pd.to_datetime(planilha['data_de_nascimento'], errors='coerce')

    print(planilha.head())  # Verificação
    inserir_no_banco(planilha)


if __name__ == "__main__":
    caminho_arquivo = os.path.join(os.getcwd(), 'planilha_colaboradores.xlsx')
    importar_planilha(caminho_arquivo)
