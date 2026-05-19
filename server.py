from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
import urllib.request

app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get('DB_PATH', 'db.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock REAL NOT NULL,
        thickness TEXT,
        icon TEXT,
        image TEXT
    )''')
    
    # Inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        qty REAL NOT NULL,
        type TEXT NOT NULL,
        date TEXT NOT NULL
    )''')
    
    # Customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        debt REAL DEFAULT 0
    )''')
    
    # Expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT
    )''')
    
    # Album Styles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS album_styles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        image TEXT
    )''')
    
    # Sales table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        total REAL NOT NULL,
        date TEXT NOT NULL,
        customerId INTEGER,
        customerName TEXT,
        paymentMethod TEXT,
        items TEXT
    )''')
    
    # Settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Insert initial data if database is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        initial_products = [
            (1, 'Tunikafon (Kafel)', 55000, 120, '0.45', '🏠', ''),
            (2, 'Tunikafon (Monterrey)', 62000, 85, '0.50', '🏠', ''),
            (3, 'Tunikafon (Klassik)', 48000, 200, '0.40', '🏠', ''),
            (4, 'Profnastil N10', 38000, 300, '0.35', '📋', ''),
            (5, 'Profnastil N20', 45000, 150, '0.45', '📋', ''),
            (6, 'Profnastil N35 (Tom)', 58000, 90, '0.50', '📋', ''),
            (7, 'Tunika (Yassi list)', 32000, 500, '0.30', '📄', '')
        ]
        cursor.executemany('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)', initial_products)
        
        initial_inventory = [
            ('Rulon List (Oq)', 1200, 'raw', '12.05.2026'),
            ('Rulon List (Shokolad)', 850, 'raw', '12.05.2026')
        ]
        cursor.executemany('INSERT INTO inventory (name, qty, type, date) VALUES (?, ?, ?, ?)', initial_inventory)
        
        cursor.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?)', (1, 'Umumiy Mijoz', '', '', 0))
        
        initial_styles = [
            (1, 'Kafel - Shokolad', ''),
            (2, 'Monterrey - Qizil', '')
        ]
        cursor.executemany('INSERT INTO album_styles VALUES (?, ?, ?)', initial_styles)
        
        cursor.execute('INSERT INTO settings VALUES (?, ?)', ('shopName', 'ERMATOV ERP'))
        cursor.execute('INSERT INTO settings VALUES (?, ?)', ('currency', "so'm"))
        
    conn.commit()
    conn.close()

# Serves frontend
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/manifest.json')
def manifest():
    return send_file('manifest.json')

@app.route('/sw.js')
def sw():
    return send_file('sw.js')

@app.route('/libs/<path:filename>')
def serve_libs(filename):
    return send_from_directory('libs', filename)

# API: Get entire state
@app.route('/api/state', methods=['GET'])
def get_state():
    conn = get_db()
    cursor = conn.cursor()
    
    products = [dict(row) for row in cursor.execute('SELECT * FROM products').fetchall()]
    inventory = [dict(row) for row in cursor.execute('SELECT * FROM inventory').fetchall()]
    customers = [dict(row) for row in cursor.execute('SELECT * FROM customers').fetchall()]
    expenses = [dict(row) for row in cursor.execute('SELECT * FROM expenses').fetchall()]
    album_styles = [dict(row) for row in cursor.execute('SELECT * FROM album_styles').fetchall()]
    sales_rows = cursor.execute('SELECT * FROM sales').fetchall()
    
    sales = []
    for row in sales_rows:
        d = dict(row)
        d['items'] = json.loads(d['items'])
        sales.append(d)
        
    settings_rows = cursor.execute('SELECT * FROM settings').fetchall()
    settings = {row['key']: row['value'] for row in settings_rows}
    
    conn.close()
    
    return jsonify({
        'products': products,
        'inventory': inventory,
        'customers': customers,
        'expenses': expenses,
        'albumStyles': album_styles,
        'sales': sales,
        'settings': settings
    })

# API: Sync Full Backup (Import Backup)
@app.route('/api/state/import', methods=['POST'])
def import_state():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute('DELETE FROM products')
        cursor.execute('DELETE FROM inventory')
        cursor.execute('DELETE FROM customers')
        cursor.execute('DELETE FROM expenses')
        cursor.execute('DELETE FROM album_styles')
        cursor.execute('DELETE FROM sales')
        cursor.execute('DELETE FROM settings')
        
        for p in data.get('products', []):
            cursor.execute('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)', 
                           (p['id'], p['name'], p['price'], p['stock'], p['thickness'], p['icon'], p.get('image', '')))
            
        for i in data.get('inventory', []):
            cursor.execute('INSERT INTO inventory (name, qty, type, date) VALUES (?, ?, ?, ?)', 
                           (i['name'], i['qty'], i['type'], i['date']))
            
        for c in data.get('customers', []):
            cursor.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?)', 
                           (c['id'], c['name'], c.get('phone', ''), c.get('address', ''), c.get('debt', 0)))
            
        for e in data.get('expenses', []):
            cursor.execute('INSERT INTO expenses (date, amount, category, note) VALUES (?, ?, ?, ?)', 
                           (e['date'], e['amount'], e['category'], e.get('note', '')))
            
        for s in data.get('albumStyles', []):
            cursor.execute('INSERT INTO album_styles VALUES (?, ?, ?)', 
                           (s['id'], s['name'], s.get('image', '')))
            
        for s in data.get('sales', []):
            cursor.execute('INSERT INTO sales (id, total, date, customerId, customerName, paymentMethod, items, archived) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                           (s['id'], s['total'], s['date'], s['customerId'], s['customerName'], s['paymentMethod'], json.dumps(s['items']), s.get('archived', 0)))
            
        settings = data.get('settings', {})
        for k, v in settings.items():
            cursor.execute('INSERT INTO settings VALUES (?, ?)', (k, str(v)))
            
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

# API: Products CRUD
@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (data['id'], data['name'], data['price'], data['stock'], data['thickness'], data['icon'], data.get('image', '')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/products/<int:pid>', methods=['PUT', 'DELETE'])
def handle_product(pid):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute('UPDATE products SET name=?, price=?, stock=?, thickness=?, icon=?, image=? WHERE id=?',
                       (data['name'], data['price'], data['stock'], data['thickness'], data['icon'], data.get('image', ''), pid))
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: Inventory CRUD
@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (name, qty, type, date) VALUES (?, ?, ?, ?)',
                   (data['name'], data['qty'], data['type'], data['date']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/inventory/<int:iid>', methods=['PUT', 'DELETE'])
def handle_inventory(iid):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute('UPDATE inventory SET qty=? WHERE id=?', (data['qty'], iid))
    elif request.method == 'DELETE':
        # In SQLite AUTOINCREMENT tables have ids, but in initial html it was an index.
        # We will handle it by Database ID
        cursor.execute('DELETE FROM inventory WHERE id=?', (iid,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: Customers CRUD
@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?)',
                   (data['id'], data['name'], data.get('phone', ''), data.get('address', ''), data.get('debt', 0)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/customers/<int:cid>', methods=['PUT', 'DELETE'])
def handle_customer(cid):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute('UPDATE customers SET name=?, phone=?, address=?, debt=? WHERE id=?',
                       (data['name'], data.get('phone', ''), data.get('address', ''), data.get('debt', 0), cid))
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM customers WHERE id=?', (cid,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: Expenses CRUD
@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO expenses (date, amount, category, note) VALUES (?, ?, ?, ?)',
                   (data['date'], data['amount'], data['category'], data.get('note', '')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/expenses/<int:eid>', methods=['DELETE'])
def delete_expense(eid):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id=?', (eid,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: Album Styles CRUD
@app.route('/api/album_styles', methods=['POST'])
def add_style():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO album_styles VALUES (?, ?, ?)',
                   (data['id'], data['name'], data.get('image', '')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/album_styles/<int:sid>', methods=['DELETE'])
def delete_style(sid):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM album_styles WHERE id=?', (sid,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: Sales (Checkout)
@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Save sale
        cursor.execute('INSERT INTO sales (id, total, date, customerId, customerName, paymentMethod, items, archived) VALUES (?, ?, ?, ?, ?, ?, ?, 0)',
                       (data['id'], data['total'], data['date'], data['customerId'], data['customerName'], data['paymentMethod'], json.dumps(data['items'])))
        
        # Update customer debt if paymentMethod is 'Nasiya'
        if data['paymentMethod'] == 'Nasiya':
            cursor.execute('UPDATE customers SET debt = debt + ? WHERE id = ?', (data['total'], data['customerId']))
            
        # Reduce product stock
        for item in data['items']:
            cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item['qty'], item['id']))
            
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

# API: Reset History (Delete Sales)
@app.route('/api/sales/reset', methods=['POST'])
def reset_sales():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sales')
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: End Day (Archive sales for today)
@app.route('/api/sales/archive', methods=['POST'])
def archive_sales():
    data = request.json
    date_str = data.get('date')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE sales SET archived = 1 WHERE date LIKE ?', (f'%{date_str}%',))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    for k, v in data.items():
        cursor.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', (k, str(v)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    # Update sales schema to include archived if not exists
    conn = get_db()
    try:
        conn.cursor().execute('ALTER TABLE sales ADD COLUMN archived INTEGER DEFAULT 0')
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column already exists
    conn.close()
    
    init_db()
    
    # Download SheetJS library if not exists
    libs_dir = 'libs'
    if not os.path.exists(libs_dir):
        os.makedirs(libs_dir)
    xlsx_path = os.path.join(libs_dir, 'xlsx.full.min.js')
    if not os.path.exists(xlsx_path):
        try:
            print("Downloading xlsx.full.min.js...")
            url = 'https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js'
            urllib.request.urlretrieve(url, xlsx_path)
            print("Download complete!")
        except Exception as e:
            print(f"Error downloading SheetJS: {e}")
            
    # Run the server
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
