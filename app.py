import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, send_file
)
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Caminho absoluto para o survey.db
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'survey.db')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_difícil')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.template_filter('format_datetime')
def format_datetime_filter(value):
    if not value:
        return ''
    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return dt.strftime('%d/%m/%Y %H:%M')


# --- LOGIN DO COLABORADOR ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        data_nascimento = request.form.get('data_nascimento', '').strip()

        if not cpf.isdigit():
            error = 'Use somente números no campo CPF.'
            return render_template('login/login.html', error=error)

        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, respondeu FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
            (cpf, data_nascimento)
        ).fetchone()
        conn.close()

        if not user:
            error = 'Dados inválidos.'
        elif user['respondeu']:
            error = 'Você já respondeu à pesquisa e não pode entrar novamente.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('pesquisa'))

    return render_template('login/login.html', error=error)


# --- FORMULÁRIO DE PESQUISA ---
@app.route('/pesquisa', methods=['GET', 'POST'])
def pesquisa():
    user_id = session.get('user_id')
    if not user_id:
        flash('Faça login antes de responder à pesquisa.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    row = conn.execute(
        'SELECT respondeu FROM colaboradores WHERE id = ?',
        (user_id,)
    ).fetchone()
    if row and row['respondeu']:
        conn.close()
        flash('Você já respondeu à pesquisa.', 'warning')
        session.pop('user_id', None)
        return redirect(url_for('login'))

    if request.method == 'POST':
        cur = conn.cursor()

        # 1) Insere um registro na tabela `respostas` (metadados)
        cur.execute('INSERT INTO respostas (data_resposta) VALUES (CURRENT_TIMESTAMP)')
        response_id = cur.lastrowid

        # 2) Itera pelas 33 perguntas e insere cada resposta em response_answers
        for qid in range(1, 34):
            ans = request.form.get(f'resposta{qid}', '').strip()
            cur.execute(
                'INSERT INTO response_answers (response_id, question_id, answer) VALUES (?, ?, ?)',
                (response_id, qid, ans)
            )

        # 3) Marca o colaborador como respondido
        cur.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (user_id,)
        )

        conn.commit()
        conn.close()

        flash('Obrigado por responder à pesquisa!', 'success')
        session.pop('user_id', None)
        return redirect(url_for('login'))

    conn.close()
    return render_template('login/pesquisa.html')


# --- LOGIN DO RH (ADMIN) ---
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM admins WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Usuário ou senha incorretos.'

    return render_template('login/admin_login.html', error=error)


# --- DASHBOARD DO RH ---
@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # aqui você pode exibir um resumo ou só o navbar
    return render_template('login/admin.html')


# --- ROTA DE LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ROTA: VISÃO ANALÍTICA ---
@app.route('/analitico')
def analitico():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    charts = []

    # busca todas as perguntas
    perguntas = conn.execute(
        'SELECT id, question_text FROM form_questions ORDER BY order_index'
    ).fetchall()

    for q in perguntas:
        # agrupa pelo texto da resposta diretamente
        rows = conn.execute(
            '''
            SELECT answer   AS option_label,
                   COUNT(*) AS cnt
              FROM response_answers
             WHERE question_id = ?
             GROUP BY answer
            ''',
            (q['id'],)
        ).fetchall()

        labels = [r['option_label'] for r in rows]
        values = [r['cnt'] for r in rows]
        total = sum(values)
        if total == 0:
            continue

        # monta o pie chart
        fig, ax = plt.subplots(figsize=(4, 4))
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct=lambda pct: f"{pct:.0f}%",
            startangle=90,
            textprops={'fontsize': 12}
        )
        ax.axis('equal')

        # gera legenda com rótulos e cores
        legend_items = []
        for w, label in zip(wedges, labels):
            legend_items.append({
                'label': label,
                'color': w.get_facecolor()
            })

        # converte imagem para base64
        buf = io.BytesIO()
        FigureCanvas(fig).print_png(buf)
        img_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        buf.close()
        plt.close(fig)

        charts.append({
            'question_text': q['question_text'],
            'count': total,
            'img_b64': img_b64,
            'legend': legend_items
        })

    conn.close()
    return render_template('login/analitico.html', charts=charts)


if __name__ == '__main__':
    app.run(debug=True, port=10000)
