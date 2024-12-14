from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('tax_tracking.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Dynamically add missing columns to the TaxRecords table
    cursor.execute("PRAGMA table_info(TaxRecords);")
    existing_columns = [column[1] for column in cursor.fetchall()]

    # Add missing columns
    if "tax_rate" not in existing_columns:
        cursor.execute("ALTER TABLE TaxRecords ADD COLUMN tax_rate REAL;")
    if "tax_due" not in existing_columns:
        cursor.execute("ALTER TABLE TaxRecords ADD COLUMN tax_due REAL;")

    # Create table if it doesn't exist
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

# Generate dynamic due dates
def get_due_dates():
    current_year = datetime.now().year
    return [
        f"{current_year}-04-15",
        f"{current_year}-06-15",
        f"{current_year}-09-15",
        f"{current_year + 1}-01-15"
    ]

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
    tax_rate = request.form.get('tax_rate')  # Optional
    payment_date = request.form.get('payment_date')
    status = request.form['status']
    due_date = request.form['due_date']

    # Calculate tax due if tax rate is provided
    tax_due = None
    if tax_rate:
        try:
            tax_rate = float(tax_rate)
            tax_due = amount * tax_rate
        except ValueError:
            tax_rate = None

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
    if due_date:
        records = conn.execute("SELECT * FROM TaxRecords WHERE due_date = ?", (due_date,)).fetchall()
    else:
        records = conn.execute("SELECT * FROM TaxRecords").fetchall()
    conn.close()

    return render_template('tax_records.html', records=records, due_dates=get_due_dates(), search_due_date=due_date)

@app.route('/tax/summary', methods=['GET'])
def tax_summary():
    due_date = request.args.get('due_date')
    tax_rate = request.args.get('tax_rate', 0.0)

    try:
        tax_rate = float(tax_rate)
    except ValueError:
        tax_rate = 0.0  # Default to 0 if invalid input

    conn = get_db_connection()
    records = conn.execute(
        "SELECT * FROM TaxRecords WHERE due_date = ?", (due_date,)
    ).fetchall()

    total_amount = sum(record['amount'] for record in records)
    tax_due = total_amount * tax_rate  # Calculate tax due based on tax rate
    conn.close()

    return jsonify({
        'records': [dict(record) for record in records],
        'total_amount': total_amount,
        'tax_rate': tax_rate,
        'tax_due': tax_due
    })

@app.route('/database', methods=['GET'])
def database_access():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM TaxRecords").fetchall()
    conn.close()
    return render_template('database_access.html', records=records)

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    init_db()

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=8080)
