import sqlite3

# agora criamos e populamos o survey.db
db_path = 'survey.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ----- Criação de tabelas -----
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

# Tabela de respostas legadas (até 11 perguntas)
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

# ----- Seed de usuários de RH -----
cursor.executemany(
  'INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)',
  [
    ('rh1', 'senha123'),
    ('rh2', 'secret456')
  ]
)

# ----- Seed das perguntas do Form Builder -----
# 32 perguntas de múltipla escolha
perguntas_mc = []
for i in range(1, 33):
    perguntas_mc.append({
        "order": i,
        "text": f"Pergunta {i}: [insira o enunciado aqui]",
        "type": "radio",
        "options": [
            ("Opção A", "A"),
            ("Opção B", "B"),
            ("Opção C", "C"),
            ("Opção D", "D"),
        ]
    })

# 33ª pergunta (discursiva)
pergunta_texto = {
    "order": 33,
    "text": "Pergunta 33 (resposta livre): [insira o enunciado aqui]",
    "type": "text",
    "options": []
}

todas_perguntas = perguntas_mc + [pergunta_texto]

for p in todas_perguntas:
    cursor.execute('''
      INSERT OR IGNORE INTO form_questions (order_index, question_text, question_type)
      VALUES (?, ?, ?)
    ''', (p["order"], p["text"], p["type"]))
    # Recupera o id da pergunta (caso já exista mantém o mesmo ID)
    cursor.execute('SELECT id FROM form_questions WHERE order_index = ?', (p["order"],))
    qid = cursor.fetchone()[0]

    # Popula opções somente para múltipla escolha
    if p["type"] == "radio":
        for label, value in p["options"]:
            cursor.execute('''
              INSERT OR IGNORE INTO form_options (question_id, option_label, option_value)
              VALUES (?, ?, ?)
            ''', (qid, label, value))

# ----- Finaliza e fecha conexão -----
conn.commit()
conn.close()
print("survey.db criado e populado com sucesso.")
