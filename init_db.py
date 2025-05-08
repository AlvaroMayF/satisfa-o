import sqlite3

def main():
    # Conecta no survey.db (ou cria, se não existir)
    conn = sqlite3.connect('survey.db')
    cursor = conn.cursor()

    # Criação da tabela de admins
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
      id       INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT    UNIQUE NOT NULL,
      password TEXT    NOT NULL
    )
    ''')

    # Criação da tabela de colaboradores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS colaboradores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT UNIQUE,
        data_nascimento TEXT,
        email TEXT,
        cargo TEXT,
        setor TEXT,
        respondeu BOOLEAN DEFAULT 0
    )
    ''')

    # (demais tabelas…)
    # respostas legadas, form_questions, form_options, responses, response_answers

    # Usuários de teste
    cursor.execute('''
    INSERT OR IGNORE INTO admins (username, password)
    VALUES ('admin', 'admin123'), ('rh', 'rh123')
    ''')

    conn.commit()
    conn.close()
    print("survey.db inicializado com sucesso.")

if __name__ == '__main__':
    main()
