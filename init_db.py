# init_db.py
import sqlite3

# agora criamos e populamos o survey.db
conn = sqlite3.connect('survey.db')
cursor = conn.cursor()

# Tabela de admins
cursor.execute('''
  CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
  )
''')

# Tabela de colaboradores
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

# Tabela de respostas legadas
cursor.execute('''
  CREATE TABLE IF NOT EXISTS respostas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resposta1 TEXT, resposta2 TEXT, resposta3 TEXT,
    resposta4 TEXT, resposta5 TEXT, resposta6 TEXT,
    resposta7 TEXT, resposta8 TEXT, resposta9 TEXT,
    resposta10 TEXT, resposta11 TEXT,
    data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
''')

# Tabelas do Form Builder
cursor.execute('''
  CREATE TABLE IF NOT EXISTS form_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL
  )
''')
cursor.execute('''
  CREATE TABLE IF NOT EXISTS form_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER REFERENCES form_questions(id) ON DELETE CASCADE,
    option_label TEXT NOT NULL,
    option_value TEXT NOT NULL
  )
''')
cursor.execute('''
  CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
''')
cursor.execute('''
  CREATE TABLE IF NOT EXISTS response_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER REFERENCES responses(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES form_questions(id) ON DELETE CASCADE,
    answer TEXT NOT NULL
  )
''')

# Usuários de RH de teste
cursor.executemany(
  'INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)',
  [
    ('rh1', 'senha123'),
    ('rh2', 'secret456')
  ]
)

conn.commit()
conn.close()
print("survey.db criado e populado com sucesso.")
