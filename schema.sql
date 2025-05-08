-- schema.sql

PRAGMA foreign_keys = ON;

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
