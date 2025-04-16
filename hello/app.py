from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import mysql.connector
import bcrypt
import os
import re 
from urllib.parse import urlparse

# Regular expressions to validate email.

app = Flask(__name__)
app.secret_key = os.urandom(24)


# MySQL Configuration
DATABASE_URL = os.environ.get('mysql://root:tVibzqhaaTvTyXoxnVpIHYUiTGHbrKVC@mysql.railway.internal:3306/railway')


if DATABASE_URL:
    url = urlparse(DATABASE_URL)
    db_config = {
        'host': url.mysql.railway.internal,
        'user': url.root,
        'password': url.tVibzqhaaTvTyXoxnVpIHYUiTGHbrKVC,
        'database': url.path[1:],
        'port':  3306,
    }
else:
     raise EnvironmentError("DATABASE_URL environment variable not set.")


def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/generate_hash')
def generate_hash():
    password = "Mukhesh@2005"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return jsonify({'hash': hashed_password.decode('utf-8')})



@app.route("/test_db")
def test_db():
    import mysql.connector
    try:
        conn = mysql.connector.connect(**db_config)
        return "Database connection successful!"
    except Exception as e:
        return f"Error: {e}"


@app.route('/', methods=['GET', 'POST'])
def default_login():
    return redirect(url_for('user_login'))

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND role = %s', (username, 'user'))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            return redirect(url_for('user_home'))
        else:
            return render_template('user_login.html', error='Invalid username or password')
    return render_template('user_login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND role = %s', (username, 'admin'))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid username or password')
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template('register.html', error='Invalid email format')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (full_name, username, email, password, role) VALUES (%s, %s, %s, %s, %s)',
                           (full_name, username, email, hashed_password, 'user'))
            conn.commit()
            return redirect(url_for('user_login')) # redirect to user login.
        except mysql.connector.Error as err:
            return render_template('register.html', error=f'Error: {err}')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/user')
def user_home():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('user_login'),)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()

    cursor.execute('SELECT * FROM blood_stocks')
    stocks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user_home.html', donors=donors, stocks=stocks)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()

    cursor.execute('SELECT * FROM messages')
    messages = cursor.fetchall()

    cursor.execute('SELECT * FROM blood_stocks')
    stocks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html', users=users, donors=donors, messages=messages, stocks=stocks)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('user_login'))

@app.route('/add_donor_page')
def add_donor_page():
    return render_template('add_donor.html')

@app.route('/search_donors_page')
def search_donors_page():
    return render_template('search_donors.html')

@app.route('/blood_stocks_page')
def blood_stocks_page():
    stocks = get_blood_stocks()
    return render_template('blood_stocks.html', stocks=stocks)

@app.route('/list_donors_page')
def list_donors_page():
    donors = get_donors()
    return render_template('list_donors.html', donors=donors)

@app.route('/add_donor', methods=['POST'])
def add_donor():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    name = request.form['name']
    address = request.form['address']
    mobile_no = request.form['mobile_no']
    blood_type = request.form['blood_type']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO donors (name, address, mobile_no, blood_type) VALUES (%s, %s, %s, %s)',
                       (name, address, mobile_no, blood_type))
        conn.commit()
        return redirect(url_for('user_home'))
    except mysql.connector.Error as err:
        return f'Error: {err}'
    finally:
        cursor.close()
        conn.close()


@app.route('/delete_donor/<int:donor_id>')
def delete_donor(donor_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM donors WHERE donor_id = %s', (donor_id,))
        conn.commit()
        return redirect(url_for('admin_dashboard'))
    except mysql.connector.Error as err:
        return f'Error: {err}'
    finally:
        cursor.close()
        conn.close()

@app.route('/update_stock/<blood_type>', methods=['POST'])
def update_stock(blood_type):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    operation = request.form.get('operation')
    units = int(request.form.get('units'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if operation == 'add':
            cursor.execute('UPDATE blood_stocks SET units = units + %s WHERE blood_type = %s', (units, blood_type))
        elif operation == 'subtract':
            cursor.execute('UPDATE blood_stocks SET units = units - %s WHERE blood_type = %s', (units, blood_type))

        conn.commit()
        return '', 204  # no content, success.
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return f'Error: {err}', 500
    finally:
        cursor.close()
        conn.close()

@app.route('/search_donors', methods=['POST'])
def search_donors():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    blood_type = request.form['blood_type']
    address = request.form['address']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = 'SELECT * FROM donors WHERE 1=1'
    params = []

    if blood_type:
        query += ' AND blood_type = %s'
        params.append(blood_type)
    if address:
        query += ' AND address LIKE %s'
        params.append(f'%{address}%')

    cursor.execute(query, params)
    donors = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('search_donors.html', donors=donors, stocks=[])

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error deleting user: {err}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_stock', methods=['POST'])
def add_stock():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    blood_type = request.form['blood_type']
    units = request.form['units']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO blood_stocks (blood_type, units) VALUES (%s, %s)', (blood_type, units))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error adding stock: {err}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_stock_type/<blood_type>')
def delete_stock_type(blood_type):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM blood_stocks WHERE blood_type = %s', (blood_type,))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error deleting stock type: {err}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

def get_blood_stocks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM blood_stocks')
    stocks = cursor.fetchall()
    cursor.close()
    conn.close()
    return stocks

def get_donors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()
    cursor.close()
    conn.close()
    return donors

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
