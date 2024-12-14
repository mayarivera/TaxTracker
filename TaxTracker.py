from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

 # connects to the sqlite database
def get_db_connection():
    conn = sqlite3.connect('tax_tracking.db')
    conn.row_factory = sqlite3.Row
    return conn

# inititalizes database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # makes sure content exists ie tables + columns
    cursor.execute("PRAGMA table_info(TaxRecords);")
    existing_columns = [column[1] for column in cursor.fetchall()]
    if "tax_rate" not in existing_columns:
        cursor.execute("ALTER TABLE TaxRecords ADD COLUMN tax_rate REAL;")
    if "tax_due" not in existing_columns:
        cursor.execute("ALTER TABLE TaxRecords ADD COLUMN tax_due REAL;")

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS TaxRecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            amount REAL NOT NULL,
            tax_rate REAL,
            tax_due REAL,
            payment_date TEXT,
            status TEXT CHECK(status IN ('paid', 'unpaid')) NOT NULL,
            due_date TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# dynamic coding - due dates
def get_due_dates():
    year = datetime.now().year
    return [f"{year}-04-15", f"{year}-06-15", f"{year}-09-15", f"{year + 1}-01-15"]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/tax/records')
def view_records():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM TaxRecords").fetchall()
    conn.close()
    return render_template('tax_records.html', records=records, due_dates=get_due_dates())

@app.route('/tax/records/add', methods=['POST'])
def add_record():
    company = request.form['company']
    amount = float(request.form['amount'])
    tax_rate = request.form.get('tax_rate')
    payment_date = request.form.get('payment_date')
    status = request.form['status']
    due_date = request.form['due_date']

    tax_due = float(amount) * float(tax_rate) if tax_rate else None

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO TaxRecords (company, amount, tax_rate, tax_due, payment_date, status, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (company, amount, tax_rate, tax_due, payment_date, status, due_date)
    )
    conn.commit()
    conn.close()
    return redirect('/tax/records')

@app.route('/tax/records/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM TaxRecords WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return redirect('/tax/records')

@app.route('/tax/records/search', methods=['GET'])
def search_records():
    due_date = request.args.get('due_date')
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM TaxRecords WHERE due_date = ?", (due_date,)).fetchall() if due_date else conn.execute("SELECT * FROM TaxRecords").fetchall()
    conn.close()
    return render_template('tax_records.html', records=records, due_dates=get_due_dates(), search_due_date=due_date)

@app.route('/database')
def database_access():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM TaxRecords").fetchall()
    conn.close()
    return render_template('database_access.html', records=records)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) #had to use this port because 5000 was being used

#Used prior project for flask outline and made alterations for project specific criteria
#Used Chatgpt, Geeks for Geeks, Github, StackOverflow, Jetbrains, Medium
#Had some trouble getting the tax rate and connecting to the port
