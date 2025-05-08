import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_dificil_de_adivinhar')
DATABASE = 'survey.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Decorator para proteger rotas admin
def admin_login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapped

# === LOGIN COLABORADOR ===
@app.route('/', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf','').strip()
        dob = request.form.get('data_nascimento','').strip()
        if not cpf.isdigit():
            error = 'Informe o CPF apenas com números.'
        else:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
                (cpf, dob)
            ).fetchone()
            conn.close()
            if user:
                session.clear()
                session['user_cpf'] = cpf
                return redirect(url_for('pesquisa', question_id=1))
            error = 'Dados inválidos.'
    return render_template('login.html', error=error)

# === FLUXO DE PESQUISA DINÂMICA ===
@app.route('/pesquisa/<int:question_id>', methods=['GET','POST'])
def pesquisa(question_id):
    if 'user_cpf' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    question = conn.execute(
        'SELECT * FROM form_questions WHERE id = ?',
        (question_id,)
    ).fetchone()
    if not question:
        conn.close()
        return redirect(url_for('login'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        # cria um response geral se primeira pergunta
        conn.execute(
            'INSERT INTO responses (cpf) VALUES (?)',
            (session['user_cpf'],)
        )
        response_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.execute(
            'INSERT INTO response_answers (response_id, question_id, answer, ) VALUES (?, ?, ?)',
            (response_id, question_id, answer)
        )
        conn.commit()
        next_q = conn.execute(
            'SELECT id FROM form_questions WHERE order_index > ? ORDER BY order_index LIMIT 1',
            (question['order_index'],)
        ).fetchone()
        conn.close()
        if next_q:
            return redirect(url_for('pesquisa', question_id=next_q['id']))
        return redirect(url_for('login'))

    options = conn.execute(
        'SELECT * FROM form_options WHERE question_id = ?',
        (question_id,)
    ).fetchall()
    conn.close()
    return render_template('pesquisa.html', question=question, options=options)

# === LOGIN ADMIN ===
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM admins WHERE username = ? AND password = ?',
            (u, p)
        ).fetchone()
        conn.close()
        if admin:
            session.clear()
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        error = 'Usuário ou senha incorretos.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# === PAINEL ADMIN ===
@app.route('/admin')
@admin_login_required
def admin_panel():
    conn = get_db_connection()
    medias = conn.execute('''
        SELECT q.id, q.question_text AS text, AVG(CAST(a.answer AS FLOAT)) AS avg_answer
        FROM form_questions q
        LEFT JOIN response_answers a ON a.question_id = q.id
        GROUP BY q.id
        ORDER BY q.order_index
    ''').fetchall()
    respostas = conn.execute('SELECT * FROM responses ORDER BY submitted_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', medias=medias, respostas=respostas)

# === FORM BUILDER ===
@app.route('/admin/form-builder', methods=['GET','POST'])
@admin_login_required
def form_builder():
    conn = get_db_connection()
    if request.method == 'POST':
        idx   = request.form.get('order_index')
        text  = request.form.get('question_text')
        qtype = request.form.get('question_type')
        if not idx or not text:
            flash('Preencha todos os campos.')
        else:
            conn.execute(
                'INSERT INTO form_questions (order_index, question_text, question_type) VALUES (?, ?, ?)',
                (int(idx), text, qtype)
            )
            conn.commit()
        return redirect(url_for('form_builder'))

    perguntas = conn.execute('SELECT * FROM form_questions ORDER BY order_index').fetchall()
    conn.close()
    return render_template('form_builder.html', perguntas=perguntas)

@app.route('/admin/form-builder/delete/<int:qid>', methods=['POST'])
@admin_login_required
def delete_question(qid):
    conn = get_db_connection()
    conn.execute('DELETE FROM form_questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for('form_builder'))

# === ERROS ===
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=10000)
