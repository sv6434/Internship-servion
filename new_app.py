from flask import Flask, request, render_template, url_for, flash,redirect
import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Initialize Flask app
new_app = Flask(__name__)
new_app.secret_key = os.getenv('SECRET_KEY')

# Database connection
def create_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Route to view records
@new_app.route("/view_records")
def view_books():
    conn = create_connection()
    records = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        flash("Failed to connect to the database.")
    return render_template("view_records.html", records=records, title="All records")

@new_app.route("/")
def home():
    return redirect(url_for('view_books'))

# Run the app
if __name__ == "__main__":
    new_app.run(debug=True)
