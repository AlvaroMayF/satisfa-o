import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

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

# Criação da tabela de respostas anônimas (11 perguntas)
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
)
''')

# Mock para testes
cursor.execute('''
INSERT OR IGNORE INTO colaboradores (
    nome, cpf, data_nascimento, email, cargo, setor
) VALUES (
    'Maria Teste', '12345678900', '1990-05-06', 'maria@empresa.com', 'RH', 'Administrativo'
)
''')

cursor.execute('''
INSERT OR IGNORE INTO colaboradores (
    id, nome, cpf, data_nascimento, email, cargo, setor
) VALUES (
    2, 'alvaro may', '01772838233', '2003-12-11',
    'alvaro.may@hospitalsamar.com.br', 'TI', 'administrativo'
)
''')


conn.commit()
conn.close()
print("Banco de dados criado com sucesso.")
