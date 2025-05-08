# init_db.py

import sqlite3

def init_db():
    with sqlite3.connect('survey.db') as conn:
        cursor = conn.cursor()

        # 1) Admins
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        ''')
        cursor.execute('''
        INSERT OR IGNORE INTO admins (username, password)
        VALUES ('admin', 'senhaTeste123');
        ''')

        # 2) Colaboradores
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
        );
        ''')

        # 3) Respostas legadas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resposta1 TEXT,
            resposta2 TEXT,
            resposta3 TEXT,
            resposta4 TEXT,
            resposta5 TEXT,
            resposta6 TEXT,
            resposta7 TEXT,
            resposta8 TEXT,
            resposta9 TEXT,
            resposta10 TEXT,
            resposta11 TEXT,
            data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # 4) Perguntas dinâmicas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS form_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_index INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL
        );
        ''')

        # 5) Opções de múltipla escolha
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS form_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            option_label TEXT NOT NULL,
            option_value TEXT NOT NULL,
            FOREIGN KEY(question_id) REFERENCES form_questions(id) ON DELETE CASCADE
        );
        ''')

        # 6) Novo fluxo de respostas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT NOT NULL,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS response_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            FOREIGN KEY(response_id) REFERENCES responses(id) ON DELETE CASCADE,
            FOREIGN KEY(question_id) REFERENCES form_questions(id) ON DELETE CASCADE
        );
        ''')

        conn.commit()
    print("✅ survey.db inicializado com sucesso!")

if __name__ == '__main__':
    init_db()
