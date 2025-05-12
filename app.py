import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
from itertools import cycle
import math

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'survey.db')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_difícil')

FIXED_COLORS = {
    'Menos de 12 meses': '#3366CC',
    'De 1 ano a 2 anos': '#FF9900',
    'De 3 anos a 4 anos': '#DC3912',
    'Acima de 5 anos': '#109618'
}

DEFAULT_COLORS = [
    '#3366CC', '#FF9900', '#DC3912', '#109618', '#990099', '#0099C6', '#DD4477',
    '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99', '#AAAA11', '#6633CC',
    '#E67300', '#8B0707', '#329262', '#5574A6', '#3B3EAC', '#FF33CC'
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def sincronizar_opcoes_conectado(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT question_id, answer FROM response_answers")
    respostas = cur.fetchall()
    novas = 0
    for question_id, resposta in respostas:
        cur.execute(
            "SELECT 1 FROM form_options WHERE question_id = ? AND option_label = ?",
            (question_id, resposta)
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO form_options (question_id, option_label, option_value) VALUES (?, ?, ?)",
                (question_id, resposta, resposta)
            )
            novas += 1
    if novas > 0:
        conn.commit()

@app.template_filter('format_datetime')
def format_datetime_filter(value):
    if not value:
        return ''
    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return dt.strftime('%d/%m/%Y %H:%M')

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
        cur.execute('INSERT INTO respostas (data_resposta) VALUES (CURRENT_TIMESTAMP)')
        response_id = cur.lastrowid
        for qid in range(1, 34):
            ans = request.form.get(f'resposta{qid}', '').strip()
            cur.execute(
                'INSERT INTO response_answers (response_id, question_id, answer) VALUES (?, ?, ?)',
                (response_id, qid, ans)
            )
        cur.execute('UPDATE colaboradores SET respondeu = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('Obrigado por responder à pesquisa!', 'success')
        session.pop('user_id', None)
        return redirect(url_for('login'))
    conn.close()
    return render_template('login/pesquisa.html')

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

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('login/admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/analitico')
def analitico():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    sincronizar_opcoes_conectado(conn)
    charts = []
    perguntas = conn.execute(
        'SELECT id, question_text FROM form_questions ORDER BY order_index'
    ).fetchall()
    for q in perguntas:
        opcoes = conn.execute(
            'SELECT DISTINCT option_label FROM form_options WHERE question_id = ? ORDER BY option_label',
            (q['id'],)
        ).fetchall()
        all_labels = [o['option_label'] for o in opcoes]
        rows = conn.execute(\
            '''
            SELECT answer AS option_label, COUNT(*) AS cnt
            FROM response_answers
            WHERE question_id = ?
            GROUP BY answer
            ''',
            (q['id'],)
        ).fetchall()
        contagem = {r['option_label']: r['cnt'] for r in rows}
        labels = all_labels
        values = [contagem.get(label, 0) for label in labels]
        values = [0 if (v is None or isinstance(v, float) and math.isnan(v)) else v for v in values]
        if sum(values) == 0:
            continue
        color_cycle = cycle(DEFAULT_COLORS)
        color_map = {label: FIXED_COLORS.get(label, next(color_cycle)) for label in labels}
        colors = [color_map[label] for label in labels]
        fig, ax = plt.subplots(figsize=(4, 4))
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            colors=colors,
            autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else '',
            startangle=90,
            textprops={'fontsize': 12}
        )
        ax.axis('equal')
        legend_items = []
        for label, value in zip(labels, values):
            if value > 0 and not label.lower().startswith('opção'):
                legend_items.append({
                    'label': label,
                    'color': color_map[label]
                })
        buf = io.BytesIO()
        FigureCanvas(fig).print_png(buf)
        img_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        buf.close()
        plt.close(fig)
        charts.append({
            'question_text': q['question_text'],
            'count': sum(values),
            'img_b64': img_b64,
            'legend': legend_items
        })
    conn.close()
    return render_template('login/analitico.html', charts=charts)

if __name__ == '__main__':
    app.run(debug=True, port=10000)
