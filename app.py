import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)

app = Flask(__name__)
# Secret key for sessions & flash messages
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_dificil_de_adivinhar')

# Path to your SQLite database
DATABASE = 'survey.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
#  Helpers / Template Filters
# -----------------------------

@app.template_filter('format_datetime')
def format_datetime(value):
    """Format a SQL datetime string into 'DD/MM/YYYY HH:MM'."""
    if not value:
        return ''
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d/%m/%Y %H:%M")


# -----------------------------
#  COLABORADOR – Login & Pesquisa
# -----------------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        dob = request.form.get('data_nascimento', '').strip()

        # Simple CPF validation
        if not cpf.isdigit():
            error = 'Informe o CPF apenas com números.'
        else:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
                (cpf, dob)
            ).fetchone()
            conn.close()

            if not user:
                error = 'Dados inválidos.'
            elif user['respondeu']:
                error = 'Você já respondeu à pesquisa.'
            else:
                # store user in session and go to first question
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('pesquisa', user_id=user['id']))

    return render_template('login/login.html', error=error)


@app.route('/pesquisa/<int:user_id>', methods=['GET', 'POST'])
def pesquisa(user_id):
    # Protect this route: only logged in users can proceed
    if session.get('user_id') != user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # fetch the question text & type from a legacy table or dynamic form_questions
    question = conn.execute(
        'SELECT * FROM form_questions WHERE id = ?', (user_id,)
    ).fetchone()
    # If no question found, redirect back to login
    if question is None:
        conn.close()
        return redirect(url_for('login'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        # save into a new responses table for dynamic form
        conn.execute(
            'INSERT INTO response_answers (response_id, question_id, answer) VALUES ('
            '(SELECT id FROM responses WHERE cpf = ?), ?, ?)',
            (session['user_id'], user_id, answer)
        )
        conn.commit()
        conn.close()
        flash('Resposta registrada!')
        # find next question
        next_q = conn.execute(
            'SELECT id FROM form_questions WHERE id > ? ORDER BY id LIMIT 1',
            (user_id,)
        ).fetchone()
        if next_q:
            return redirect(url_for('pesquisa', user_id=next_q['id']))
        # if no more questions, mark colaborador as responded
        conn = get_db_connection()
        conn.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        session.clear()
        return render_template('login/thank_you.html')

    # For GET, fetch options for this question
    options = conn.execute(
        'SELECT * FROM form_options WHERE question_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    return render_template(
        'pesquisa.html',
        question=question,
        options=options
    )


# -----------------------------
#  ADMIN – Login, Painel & Logout
# -----------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # If already logged in, go straight to /admin
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        dob = request.form.get('data_nascimento', '').strip()

        # simple validation
        if not cpf.isdigit():
            error = 'Use somente números no campo CPF.'
        # authorized RH users hard-coded
        elif (cpf == '12345678900' and dob == '1980-05-15') \
             or (cpf == '98765432100' and dob == '1975-10-30'):
            session.clear()
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Credenciais inválidas para o RH.'

    return render_template('login/admin_login.html', error=error)


@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    # fetch all historic responses
    respostas = conn.execute(
        'SELECT r.*, c.nome FROM response_answers r '
        'JOIN responses s ON r.response_id = s.id '
        'JOIN colaboradores c ON s.cpf = c.cpf '
        'ORDER BY s.submitted_at DESC'
    ).fetchall()

    # calculate averages for each question
    medias = []
    for i in range(1, 12):
        col = f"resposta{i}"
        avg = conn.execute(
            f"SELECT AVG(CAST({col} AS FLOAT)) as media FROM response_answers"
        ).fetchone()['media']
        medias.append(round(avg, 2) if avg is not None else 0)
    conn.close()

    return render_template('admin/admin.html', respostas=respostas, medias=medias)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


# -----------------------------
#  ERRO HANDLERS
# -----------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# -----------------------------
#  RUN
# -----------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
