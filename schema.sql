-- schema.sql
PRAGMA foreign_keys = ON;

-- Usuários de admin (login)
CREATE TABLE IF NOT EXISTS admins (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT    UNIQUE NOT NULL,
  password TEXT    NOT NULL
);

-- Colaboradores (controle de quem respondeu)
CREATE TABLE IF NOT EXISTS colaboradores (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  nome            TEXT,
  cpf             TEXT    UNIQUE,
  data_nascimento TEXT,
  email           TEXT,
  cargo           TEXT,
  setor           TEXT,
  respondeu       BOOLEAN DEFAULT 0
);

-- Respostas anônimas de pesquisas legadas (11 perguntas)
CREATE TABLE IF NOT EXISTS respostas (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  resposta1     TEXT,
  resposta2     TEXT,
  resposta3     TEXT,
  resposta4     TEXT,
  resposta5     TEXT,
  resposta6     TEXT,
  resposta7     TEXT,
  resposta8     TEXT,
  resposta9     TEXT,
  resposta10    TEXT,
  resposta11    TEXT,
  data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Perguntas dinâmicas (Form Builder)
CREATE TABLE IF NOT EXISTS form_questions (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  order_index    INTEGER NOT NULL,
  question_text  TEXT    NOT NULL,
  question_type  TEXT    NOT NULL    -- ex: "radio", "checkbox", "textarea"
);

-- Opções para as perguntas de múltipla escolha
CREATE TABLE IF NOT EXISTS form_options (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id  INTEGER NOT NULL
               REFERENCES form_questions(id)
               ON DELETE CASCADE,
  option_label TEXT    NOT NULL,
  option_value TEXT    NOT NULL
);

-- Registra cada envio do novo form
CREATE TABLE IF NOT EXISTS responses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  cpf           TEXT    NOT NULL,
  submitted_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Respostas individuais do novo form
CREATE TABLE IF NOT EXISTS response_answers (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  response_id   INTEGER NOT NULL
               REFERENCES responses(id)
               ON DELETE CASCADE,
  question_id   INTEGER NOT NULL
               REFERENCES form_questions(id)
               ON DELETE CASCADE,
  answer        TEXT    NOT NULL
);
