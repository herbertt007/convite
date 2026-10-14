from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pymysql
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'troque-por-uma-chave-segura')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def get_db():
    ssl_config = {'ssl': {}} if os.environ.get('MYSQL_SSL') else None
    conn = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'convite'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl_config,
        connect_timeout=10,
        autocommit=False
    )
    return conn


def init_db():
    conn = get_db()
    with conn.cursor() as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS confirmacoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                telefone VARCHAR(50),
                numero_pessoas INT DEFAULT 1,
                mensagem TEXT,
                data_confirmacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip VARCHAR(50)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        ''')
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/confirmar', methods=['POST'])
def confirmar():
    data = request.get_json()
    nome = data.get('nome', '').strip()
    telefone = data.get('telefone', '').strip()
    numero_pessoas = data.get('numero_pessoas', 1)
    mensagem = data.get('mensagem', '').strip()

    if not nome:
        return jsonify({'success': False, 'message': 'Nome é obrigatório!'})

    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute(
                'SELECT id FROM confirmacoes WHERE nome = %s AND telefone = %s',
                (nome, telefone)
            )
            existe = c.fetchone()

            if existe:
                return jsonify({'success': False, 'message': 'Você já confirmou presença!'})

            ip = request.remote_addr
            c.execute(
                'INSERT INTO confirmacoes (nome, telefone, numero_pessoas, mensagem, ip) VALUES (%s, %s, %s, %s, %s)',
                (nome, telefone, numero_pessoas, mensagem, ip)
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': f'Presença confirmada! Obrigado, {nome}!'})


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'Senha incorreta!'
    return render_template('admin_login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_panel():
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute('SELECT * FROM confirmacoes ORDER BY data_confirmacao DESC')
            confirmacoes = c.fetchall()
            c.execute('SELECT COUNT(*) as total FROM confirmacoes')
            total_pessoas_row = c.fetchone()
            c.execute('SELECT SUM(numero_pessoas) as soma FROM confirmacoes')
            soma_row = c.fetchone()
    finally:
        conn.close()

    total_confirmacoes = total_pessoas_row['total'] if total_pessoas_row else 0
    total_pessoas = soma_row['soma'] if soma_row and soma_row['soma'] else 0

    return render_template('admin.html',
                           confirmacoes=confirmacoes,
                           total_confirmacoes=total_confirmacoes,
                           total_pessoas=total_pessoas)


@app.route('/admin/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_confirmacao(id):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute('DELETE FROM confirmacoes WHERE id = %s', (id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/api/lista')
@login_required
def api_lista():
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute('SELECT * FROM confirmacoes ORDER BY data_confirmacao DESC')
            rows = c.fetchall()
    finally:
        conn.close()
    return jsonify(rows)


if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
