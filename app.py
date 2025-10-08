"""
SaneX Web - Flask + SQLite
Web-based application for Masters, Entries (Production/Sale) and Reports.

Usage:
  python app.py

Login:
  Username = Admin
  Password = Admin
"""

import sqlite3
import os
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'sanex-web-secret-key-2024-change-in-production'

# Database configuration
APP_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(APP_DIR, "Data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "database.db")

# Simple password hashing
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(hashed_password, user_password):
    return hashed_password == hash_password(user_password)

# Add this function to check user permissions
def check_user_permission():
    """Check if user has permission to access the current page"""
    if 'user_id' not in session:
        return False
    
    # Admin has access to everything
    if session.get('user_role') == 'admin':
        return True
    
    # Users can only access dashboard, masters, production entries, and help
    allowed_routes = ['dashboard', 'masters', 'entries', 'help', 'logout', 'api_save_production']
    return request.endpoint in allowed_routes

# Authentication decorators
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        
        if not check_user_permission():
            flash('Access denied. You do not have permission to view this page.', 'error')
            return redirect(url_for('dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function
# def login_required(f):
#     from functools import wraps
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             flash('Please log in to access this page', 'error')
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# Database helpers
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    
    # Create tables
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT DEFAULT 'user'
    );

    CREATE TABLE IF NOT EXISTS operators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        mobile TEXT,
        address TEXT,
        created_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        mobile TEXT,
        address TEXT,
        created_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        remarks TEXT,
        created_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        created_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS productions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT,
        date TEXT,
        shift TEXT,
        operator_id INTEGER,
        data TEXT,
        created_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT,
        date TEXT,
        party_id INTEGER,
        data TEXT,
        created_at TEXT
    );
    """)
    conn.commit()

    # Create default Admin user
    cur.execute("SELECT id FROM users WHERE username = ?", ("Admin",))
    if cur.fetchone() is None:
        pw_hash = hash_password("Admin")
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                   ("Admin", pw_hash, "admin"))
        conn.commit()
    
    conn.close()

# Database functions
def list_master(table: str):
    conn = get_conn()
    cur = conn.cursor()
    if table == "operators": 
        cur.execute("SELECT * FROM operators ORDER BY id DESC")
    elif table == "parties": 
        cur.execute("SELECT * FROM parties ORDER BY id DESC")
    elif table == "machines": 
        cur.execute("SELECT * FROM machines ORDER BY id DESC")
    elif table == "items": 
        cur.execute("SELECT * FROM items ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_master(table: str, payload: dict):
    payload["created_at"] = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    try:
        if table == "operators":
            cur.execute("INSERT INTO operators (name,mobile,address,created_at) VALUES (?,?,?,?)",
                        (payload.get("name"), payload.get("mobile"), payload.get("address"), payload["created_at"]))
        elif table == "parties":
            cur.execute("INSERT INTO parties (name,mobile,address,created_at) VALUES (?,?,?,?)",
                        (payload.get("name"), payload.get("mobile"), payload.get("address"), payload["created_at"]))
        elif table == "machines":
            cur.execute("INSERT INTO machines (name,remarks,created_at) VALUES (?,?,?)",
                        (payload.get("name"), payload.get("remarks"), payload["created_at"]))
        elif table == "items":
            cur.execute("INSERT INTO items (name,type,created_at) VALUES (?,?,?)",
                        (payload.get("name"), payload.get("type"), payload["created_at"]))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_master(table: str, record_id: int):
    conn = get_conn()
    cur = conn.cursor()
    if table == "operators": 
        cur.execute("DELETE FROM operators WHERE id=?", (record_id,))
    elif table == "parties": 
        cur.execute("DELETE FROM parties WHERE id=?", (record_id,))
    elif table == "machines": 
        cur.execute("DELETE FROM machines WHERE id=?", (record_id,))
    elif table == "items": 
        cur.execute("DELETE FROM items WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def get_next_production_number():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT number FROM productions ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            num = int(row["number"][2:]) + 1
            return f"DP{num:03d}"
        except:
            return "DP001"
    return "DP001"

def get_next_sale_number():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT order_no FROM sales ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            num = int(row["order_no"][3:]) + 1
            return f"JOB{num:03d}"
        except:
            return "JOB001"
    return "JOB001"

def save_production(number, date, shift, operator_id, entries):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO productions (number,date,shift,operator_id,data,created_at) VALUES (?,?,?,?,?,?)",
                (number, date, shift, operator_id, str(entries), datetime.utcnow().isoformat()))
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

def save_sale(order_no, date, party_id, entries):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sales (order_no,date,party_id,data,created_at) VALUES (?,?,?,?,?)",
                (order_no, date, party_id, str(entries), datetime.utcnow().isoformat()))
    conn.commit()
    last = cur.lastrowid
    conn.close()
    return last

def list_productions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, o.name as operator_name 
        FROM productions p 
        LEFT JOIN operators o ON p.operator_id=o.id 
        ORDER BY p.date DESC, p.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def list_sales():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, pt.name as party_name 
        FROM sales s 
        LEFT JOIN parties pt ON s.party_id=pt.id 
        ORDER BY s.date DESC, s.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_production_totals():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT data FROM productions")
    rows = cur.fetchall()
    conn.close()
    
    total_length = 0
    total_weight = 0
    total_items = 0
    
    for row in rows:
        try:
            items_data = eval(row["data"]) if row["data"] else []
            for item in items_data:
                total_length += float(item.get("length", 0))
                total_weight += float(item.get("weight", 0))
                total_items += 1
        except:
            continue
    
    return {
        "total_length": total_length,
        "total_weight": total_weight,
        "total_items": total_items
    }

def get_sales_totals():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT data FROM sales")
    rows = cur.fetchall()
    conn.close()
    
    total_amount = 0
    total_items = 0
    total_orders = len(rows)
    
    for row in rows:
        try:
            items_data = eval(row["data"]) if row["data"] else []
            for item in items_data:
                total_amount += float(item.get("amount", 0))
                total_items += 1
        except:
            continue
    
    return {
        "total_amount": total_amount,
        "total_items": total_items,
        "total_orders": total_orders
    }

# User management functions
def add_user(username, password, role="user"):
    conn = get_conn()
    cur = conn.cursor()
    pw_hash = hash_password(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                   (username, pw_hash, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def list_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        user_data = cur.fetchone()
        conn.close()
        
        if user_data and check_password(user_data['password_hash'], password):
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['user_role'] = user_data['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    operators = list_master("operators")
    parties = list_master("parties")
    prod_totals = get_production_totals()
    sale_totals = get_sales_totals()
    
    return render_template('dashboard.html', 
                         operators=operators,
                         parties=parties,
                         prod_totals=prod_totals,
                         sale_totals=sale_totals)

@app.route('/masters')
@login_required
def masters():
    operators = list_master("operators")
    parties = list_master("parties")
    machines = list_master("machines")
    items = list_master("items")
    
    return render_template('masters.html', 
                         operators=operators, 
                         parties=parties, 
                         machines=machines, 
                         items=items)

@app.route('/api/add_master', methods=['POST'])
@login_required
def api_add_master():
    table = request.json.get('table')
    data = request.json.get('data')
    
    if add_master(table, data):
        return jsonify({'success': True, 'message': f'{table[:-1].title()} added successfully'})
    else:
        return jsonify({'success': False, 'message': f'{table[:-1].title()} name must be unique'})

@app.route('/api/delete_master', methods=['POST'])
@login_required
def api_delete_master():
    table = request.json.get('table')
    record_id = request.json.get('id')
    
    delete_master(table, record_id)
    return jsonify({'success': True, 'message': 'Record deleted successfully'})

@app.route('/entries')
@login_required
def entries():
    operators = list_master("operators")
    parties = list_master("parties")
    machines = list_master("machines")
    items = list_master("items")
    
    next_prod = get_next_production_number()
    next_sale = get_next_sale_number()
    today = datetime.today().strftime('%Y-%m-%d')
    
    user_role = session.get('user_role', 'user')
    
    return render_template('entries.html', 
                         operators=operators,
                         parties=parties,
                         machines=machines,
                         items=items,
                         next_prod=next_prod,
                         next_sale=next_sale,
                         today=today,
                         user_role=user_role)

@app.route('/api/save_production', methods=['POST'])
@login_required
def api_save_production():
    try:
        data = request.json
        production_id = save_production(
            data['number'],
            data['date'],
            data['shift'],
            data['operator_id'],
            data['items']
        )
        return jsonify({'success': True, 'id': production_id, 'message': 'Production saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/save_sale', methods=['POST'])
@login_required
def api_save_sale():
    try:
        data = request.json
        sale_id = save_sale(
            data['order_no'],
            data['date'],
            data['party_id'],
            data['items']
        )
        return jsonify({'success': True, 'id': sale_id, 'message': 'Sale saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/reports')
@login_required
def reports():
    productions = list_productions()
    sales = list_sales()
    
    prod_totals = get_production_totals()
    sale_totals = get_sales_totals()
    
    return render_template('reports.html',
                         productions=productions,
                         sales=sales,
                         prod_totals=prod_totals,
                         sale_totals=sale_totals)

@app.route('/help')
@login_required
def help():
    users = []
    if session.get('user_role') == 'admin':
        users = list_users()
    return render_template('help.html', users=users)

@app.route('/api/add_user', methods=['POST'])
@login_required
@admin_required
def api_add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role', 'user')
    
    if add_user(username, password, role):
        return jsonify({'success': True, 'message': 'User added successfully'})
    else:
        return jsonify({'success': False, 'message': 'Username already exists'})

@app.route('/api/delete_user', methods=['POST'])
@login_required
@admin_required
def api_delete_user():
    user_id = request.json.get('id')
    delete_user(user_id)
    return jsonify({'success': True, 'message': 'User deleted successfully'})

# Template filter for eval
@app.template_filter('eval')
def eval_filter(s):
    try:
        return eval(s) if s else []
    except:
        return []

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    print("\n" + "="*50)
    print("SaneX Web Application Started Successfully!")
    print("Access the application at: http://localhost:5000")
    print("Default login credentials:")
    print("Username: Admin")
    print("Password: Admin")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)