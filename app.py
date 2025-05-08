import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Cria a app e configura a secret key para proteger sessões e cookies
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_difícil_de_adivinhar')

# Banco de dados
DATABASE = 'survey.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ROTAS COLABORADOR

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        dob = request.form.get('dob', '').strip()
        # validação simples de CPF: somente dígitos
        if not cpf.isdigit():
            error = 'Informe o CPF apenas com números.'
        else:
            # aqui você pode checar se já respondeu, etc.
            session.clear()
            session['user_cpf'] = cpf
            session['user_dob'] = dob
            return redirect(url_for('pesquisa', question_id=1))
    return render_template('login.html', error=error)

@app.route('/pesquisa/<int:question_id>', methods=['GET', 'POST'])
def pesquisa(question_id):
    if 'user_cpf' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Carrega pergunta atual
    q = conn.execute('SELECT * FROM form_questions WHERE id = ?', (question_id,)).fetchone()
    if not q:
        conn.close()
        return redirect(url_for('login'))
    # Se for POST, salva resposta e redireciona
    if request.method == 'POST':
        answer = request.form.get('answer')
        conn.execute(
            'INSERT INTO responses (question_id, cpf, answer, created_at) VALUES (?, ?, ?, ?)',
            (question_id, session['user_cpf'], answer, datetime.now())
        )
        conn.commit()
        conn.close()
        next_q = conn.execute('SELECT id FROM form_questions WHERE id > ? ORDER BY id LIMIT 1', (question_id,)).fetchone()
        if next_q:
            return redirect(url_for('pesquisa', question_id=next_q['id']))
        flash('Obrigado! Suas respostas foram enviadas.')
        return redirect(url_for('login'))

    # CARREGA opções de resposta
    opts = conn.execute('SELECT * FROM form_options WHERE question_id = ?', (question_id,)).fetchall()
    conn.close()
    return render_template('pesquisa.html', question=q, options=opts)

# ROTAS ADMIN

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        # Usuários de teste
        if username == 'rh' and password == 'rh123' or username == 'admin' and password == 'admin123':
            session.clear()
            session['admin_logged_in'] = True
            return render_template('admin_login.html')
        else:
            error = 'Usuário ou senha incorretos.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    # Médias
    medias = conn.execute('''
        SELECT q.id, q.text, AVG(r.answer) as avg_answer
        FROM form_questions q
        LEFT JOIN responses r ON r.question_id = q.id
        GROUP BY q.id
        ORDER BY q.id
    ''').fetchall()
    # Todas as respostas
    respostas = conn.execute('SELECT id, created_at FROM responses GROUP BY id, created_at ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', medias=medias, respostas=respostas)

# FORM BUILDER

@app.route('/admin/form-builder', methods=['GET', 'POST'])
def form_builder():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    if request.method == 'POST':
        # adiciona nova pergunta
        idx = request.form.get('order_index')
        text = request.form.get('question_text')
        qtype = request.form.get('question_type')
        if not idx or not text:
            flash('Preencha todos os campos.')
        else:
            conn.execute(
                'INSERT INTO form_questions (id, text, type) VALUES (?, ?, ?)',
                (int(idx), text, qtype)
            )
            conn.commit()
        return redirect(url_for('form_builder'))

    perguntas = conn.execute('SELECT * FROM form_questions ORDER BY id').fetchall()
    conn.close()
    return render_template('form_builder.html', perguntas=perguntas)

@app.route('/admin/form-builder/delete/<int:qid>', methods=['POST'])
def delete_question(qid):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM form_questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for('form_builder'))

# ERROS

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=10000)
