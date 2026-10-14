from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'troque-por-uma-chave-segura')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def get_db():
    database_url = os.environ.get('DATABASE_URL', '')
    # Render usa 'postgres://' mas psycopg2 exige 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    conn = psycopg2.connect(database_url)
    return conn


def init_db():
    conn = get_db()
    with conn.cursor() as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS confirmacoes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                telefone VARCHAR(50),
                numero_pessoas INTEGER DEFAULT 1,
                mensagem TEXT,
                data_confirmacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip VARCHAR(50)
            )
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
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as c:
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
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as c:
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
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as c:
            c.execute('SELECT * FROM confirmacoes ORDER BY data_confirmacao DESC')
            rows = c.fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
