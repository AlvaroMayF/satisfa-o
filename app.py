import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_string_bem_grande_e_difícil')

DATABASE = 'survey.db'

# Credenciais de teste para o RH
RH_CREDENTIALS = {
    "rh1": "senha123",
    "rh2": "secret456"
}

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
            return render_template('./login/login.html', error=error)

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM colaboradores WHERE cpf = ? AND data_nascimento = ?',
            (cpf, data_nascimento)
        ).fetchone()

        if user:
            if user['respondeu']:
                error = 'Você já respondeu à pesquisa.'
            else:
                conn.close()
                return redirect(url_for('pesquisa', user_id=user['id']))
        else:
            error = 'Dados inválidos.'

        conn.close()

    return render_template('./login/login.html', error=error)

@app.route('/pesquisa/<int:user_id>', methods=['GET', 'POST'])
def pesquisa(user_id):
    if request.method == 'POST':
        respostas = [request.form.get(f'resposta{i}') for i in range(1, 12)]

        conn = get_db_connection()
        conn.execute(''' 
            INSERT INTO respostas (
                resposta1, resposta2, resposta3, resposta4, resposta5, resposta6,
                resposta7, resposta8, resposta9, resposta10, resposta11
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', respostas)

        conn.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        return 'Obrigado por sua resposta!'

    return render_template('login/pesquisa.html', user_id=user_id)

# Lista de dois RH autorizados (CPF sem pontuação)
RH_USERS = {
    "12345678900": "1980-05-15",
    "98765432100": "1975-10-30"
}

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()  # Usar "username" ao invés de "cpf"
        password = request.form.get('password', '').strip()  # Usar "password" ao invés de "data_nascimento"

        # Validação de usuários e senhas
        if username in RH_USERS and RH_USERS[username] == password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))  # Redireciona para o painel de administração
        else:
            error = 'Usuário ou senha incorretos.'  # Mensagem de erro

    return render_template('login/admin_login.html', error=error)

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))  # Caso não esteja logado, redireciona para o login

    conn = get_db_connection()
    respostas = conn.execute(
        'SELECT * FROM respostas ORDER BY data_resposta DESC'
    ).fetchall()

    medias = []
    for i in range(1, 9):
        coluna = f"resposta{i}"
        result = conn.execute(
            f'SELECT AVG(CAST({coluna} AS FLOAT)) as media FROM respostas'
        ).fetchone()
        medias.append(round(result['media'], 2) if result['media'] is not None else 0)

    conn.close()

    # Gerar gráficos de pizza
    charts = []
    questions = conn.execute('SELECT * FROM form_questions ORDER BY order_index').fetchall()
    for q in questions:
        opts = conn.execute(
            'SELECT option_label, COUNT(ra.id) AS cnt '
            'FROM form_options o '
            'LEFT JOIN response_answers ra '
            '  ON ra.question_id = o.question_id AND ra.answer = o.option_value '
            'WHERE o.question_id = ? '
            'GROUP BY o.id',
            (q['id'],)
        ).fetchall()

        labels = [o['option_label'] for o in opts]
        values = [o['cnt'] for o in opts]

        # Criando o gráfico
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Torna o gráfico circular

        # Salvando a imagem do gráfico
        img = io.BytesIO()
        FigureCanvas(fig).print_png(img)
        img.seek(0)
        charts.append({
            'id': q['id'],
            'text': q['question_text'],
            'img': img
        })

    return render_template('admin.html', charts=charts, respostas=respostas, medias=medias)

@app.route('/admin/chart/<int:chart_id>')
def chart(chart_id):
    chart = next((chart for chart in charts if chart['id'] == chart_id), None)
    if not chart:
        return "Gráfico não encontrado", 404
    return send_file(chart['img'], mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=10000)
