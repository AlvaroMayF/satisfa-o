import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

# ------------------------------------------------------------------------------
# Configurações iniciais
# ------------------------------------------------------------------------------
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY',
                          'uma_string_bem_grande_e_dificil_de_adivinhar')
DATABASE = 'survey.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------------------------------------------------------------
# Decorator para proteger rotas admin
# ------------------------------------------------------------------------------
def admin_login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_view

# ------------------------------------------------------------------------------
# Filtro Jinja para formatar datas
# ------------------------------------------------------------------------------
@app.template_filter('format_datetime')
def format_datetime(value):
    if not value:
        return ''
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d/%m/%Y %H:%M")

# ------------------------------------------------------------------------------
# ROTA: Login do colaborador
# ------------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf','').strip()
        dob = request.form.get('data_nascimento','').strip()

        if not cpf.isdigit():
            error = 'Use somente números no CPF.'
        else:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
                (cpf, dob)
            ).fetchone()
            conn.close()

            if not user:
                error = 'CPF ou data incorretos.'
            elif user['respondeu']:
                error = 'Você já respondeu à pesquisa.'
            else:
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('pesquisa', question_id=1))

    return render_template('login/login.html', error=error)

# ------------------------------------------------------------------------------
# ROTA: Pesquisa (protegida)
# ------------------------------------------------------------------------------
@app.route('/pesquisa/<int:question_id>', methods=['GET','POST'])
def pesquisa(question_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    q = conn.execute(
        'SELECT * FROM form_questions WHERE id = ?',
        (question_id,)
    ).fetchone()

    if not q:
        conn.close()
        flash('Pergunta não encontrada.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        # grava o envio geral
        conn.execute(
            'INSERT INTO responses (cpf, submitted_at) VALUES (?, ?)',
            (session['user_id'], datetime.now())
        )
        resp_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        # grava a resposta individual
        conn.execute(
            'INSERT INTO response_answers '
            '(response_id, question_id, answer) VALUES (?, ?, ?)',
            (resp_id, question_id, answer)
        )
        conn.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (session['user_id'],)
        )
        conn.commit()

        # próximo id
        nxt = conn.execute(
            'SELECT id FROM form_questions WHERE id > ? ORDER BY id LIMIT 1',
            (question_id,)
        ).fetchone()
        conn.close()

        if nxt:
            return redirect(url_for('pesquisa', question_id=nxt['id']))
        flash('Obrigado! Pesquisa concluída.')
        return redirect(url_for('login'))

    opts = conn.execute(
        'SELECT * FROM form_options WHERE question_id = ?',
        (question_id,)
    ).fetchall()
    conn.close()
    return render_template('pesquisa.html', question=q, options=opts)

# ------------------------------------------------------------------------------
# ROTA: Login do RH/Admin
# ------------------------------------------------------------------------------
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()

        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM admins WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()

        if not admin:
            error = 'Usuário não cadastrado.'
        elif password != admin['password']:
            error = 'Senha incorreta.'
        else:
            session.clear()
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))

    return render_template('login/admin_login.html', error=error)

@app.route('/admin/logout')
@admin_login_required
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ------------------------------------------------------------------------------
# ROTA: Painel Admin
# ------------------------------------------------------------------------------
@app.route('/admin')
@admin_login_required
def admin_panel():
    conn = get_db_connection()
    medias = conn.execute('''
        SELECT q.id,
               q.question_text AS text,
               AVG(CAST(a.answer AS REAL)) AS avg_answer
        FROM form_questions q
        LEFT JOIN response_answers a
          ON a.question_id = q.id
        GROUP BY q.id
        ORDER BY q.id
    ''').fetchall()

    respostas = conn.execute('''
        SELECT r.id, r.submitted_at
        FROM responses r
        ORDER BY r.submitted_at DESC
    ''').fetchall()
    conn.close()

    return render_template('login/admin.html',
                           medias=medias,
                           respostas=respostas)

# ------------------------------------------------------------------------------
# FORM BUILDER
# ------------------------------------------------------------------------------
@app.route('/admin/form-builder', methods=['GET','POST'])
@admin_login_required
def form_builder():
    conn = get_db_connection()
    if request.method == 'POST':
        idx = request.form.get('order_index')
        txt = request.form.get('question_text')
        typ = request.form.get('question_type')
        if not idx or not txt or not typ:
            flash('Preencha todos os campos.')
        else:
            conn.execute(
                'INSERT INTO form_questions (order_index,question_text,question_type) '
                'VALUES (?, ?, ?)',
                (int(idx), txt, typ)
            )
            conn.commit()
        return redirect(url_for('form_builder'))

    perguntas = conn.execute(
        'SELECT * FROM form_questions ORDER BY order_index'
    ).fetchall()
    conn.close()
    return render_template('form_builder.html', perguntas=perguntas)

@app.route('/admin/form-builder/delete/<int:qid>', methods=['POST'])
@admin_login_required
def delete_question(qid):
    conn = get_db_connection()
    conn.execute('DELETE FROM form_options WHERE question_id = ?', (qid,))
    conn.execute('DELETE FROM form_questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()
    return redirect(url_for('form_builder'))

# ------------------------------------------------------------------------------
# Tratamento de erros
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ------------------------------------------------------------------------------
# Inicialização do servidor
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
