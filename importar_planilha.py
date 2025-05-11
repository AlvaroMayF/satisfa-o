import os
import pandas as pd
import sqlite3

def importar_colaboradores(caminho_arquivo: str):
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return

    # 1) lê a planilha
    df = pd.read_excel(caminho_arquivo)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # 2) formata data e cpf
    if 'data_de_nascimento' in df.columns:
        df['data_de_nascimento'] = pd.to_datetime(
            df['data_de_nascimento'], errors='coerce'
        ).dt.strftime('%Y-%m-%d')
    df['cpf'] = df['cpf'].astype(str).str.replace(r'\D+', '', regex=True)

    # 3) insere no banco
    conn = sqlite3.connect('survey.db')
    cursor = conn.cursor()

    for _, row in df.iterrows():
        nome = row.get('nome', '').strip()
        cpf  = row.get('cpf', '')
        data_nascimento = row.get('data_de_nascimento', None)
        email  = row.get('email', '').strip()   # caso exista
        cargo  = row.get('funcao_inicial', '').strip()
        setor  = row.get('setor', '').strip()   # caso exista

        cursor.execute('''
            INSERT OR IGNORE INTO colaboradores
              (nome, cpf, data_nascimento, email, cargo, setor)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, cpf, data_nascimento, email, cargo, setor))

    conn.commit()
    conn.close()
    print("Colaboradores importados com sucesso!")

if __name__ == "__main__":
    caminho = os.path.join(os.getcwd(), 'planilha_colaboradores.xlsx')
    importar_colaboradores(caminho)
