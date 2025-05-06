from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'database.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.template_filter('format_datetime')
def format_datetime(value):
    if not value:
        return ''
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d/%m/%Y %H:%M")


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form['cpf'].strip()
        data_nascimento = request.form['data_nascimento']

        if not cpf.isdigit():
            error = 'Use somente números no campo CPF.'
            return render_template('login.html', error=error)

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
            (cpf, data_nascimento)
        ).fetchone()

        if user:
            if user['respondeu']:
                error = 'Você já respondeu à pesquisa.'
            else:
                return redirect(url_for('pesquisa', user_id=user['id']))
        else:
            error = 'Dados inválidos.'
        conn.close()

    return render_template('login.html', error=error)


@app.route('/pesquisa/<int:user_id>', methods=['GET', 'POST'])
def pesquisa(user_id):
    if request.method == 'POST':
        respostas = [request.form.get(f'resposta{i}') for i in range(1, 12)]

        conn = get_db_connection()

        # Grava resposta de forma anônima
        conn.execute('''
            INSERT INTO respostas (
                resposta1, resposta2, resposta3, resposta4, resposta5, resposta6,
                resposta7, resposta8, resposta9, resposta10, resposta11
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', respostas)

        # Atualiza flag de controle
        conn.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (user_id,)
        )

        conn.commit()
        conn.close()
        return 'Obrigado por sua resposta!'

    return render_template('pesquisa.html', user_id=user_id)


@app.route('/admin')
def admin():
    conn = get_db_connection()

    # Obtém todas as respostas
    respostas = conn.execute('SELECT * FROM respostas ORDER BY data_resposta DESC').fetchall()

    # Calcula média das respostas 1 a 8
    medias = []
    for i in range(1, 9):
        coluna = f"resposta{i}"
        result = conn.execute(f'SELECT AVG(CAST({coluna} AS FLOAT)) as media FROM respostas').fetchone()
        medias.append(round(result['media'], 2) if result['media'] is not None else 0)

    conn.close()
    return render_template('admin.html', respostas=respostas, medias=medias)


import os
port = int(os.environ.get("PORT", 10000))
app.run(host='0.0.0.0', port=port)

