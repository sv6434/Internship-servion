from flask import Flask, request, render_template, flash, url_for, redirect
import mysql.connector
import os
from dotenv import load_dotenv
from db_test_config import DB_CONFIG
from schema_healer import get_actual_table_name, get_salary_column_name

# Load environment variables
load_dotenv('.env')
# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Production DB connection
def create_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Test DB connection
def DB2_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Welcome page
@app.route("/")
def welcome():
    return render_template("welcome.html")
#View the datatype of each column present in the database table
@app.route("/view_datatypes")
def view_datatypes():
    conn=create_connection()
    rec=[]
    if conn:
        cursor=conn.cursor()
        cursor.execute("DESCRIBE players")
        rec=cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        flash("Failed to connect to database")
    return render_template("view_datatypes.html",rec=rec,title="Datatypes of each column present in the table.")
# View original database records
@app.route("/view_records")
def view_records():
    conn = create_connection()
    records = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        flash("Failed to connect to database.")
    return render_template("view_records.html", records=records, title="All Australian players from CSK.")

# View the records used for testing
@app.route("/view_players")
def view_test_records():
    conn = DB2_connection()
    players = []
    table_name=get_actual_table_name()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        players = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        flash("Failed to connect to database")
    return render_template("view_players.html", players=players, title="Test case table.")
#Inserting new records in the table
@app.route("/insert",methods=["GET"])
def insert_page():
    table_name = get_actual_table_name()
    salary_column = get_salary_column_name(table_name)
    return render_template("insert.html",salary_column=salary_column)
#Adding
@app.route("/add", methods=["POST"])
def add_players():
    table_name = get_actual_table_name()
    salary_column = get_salary_column_name(table_name)

    player_id = request.form["id"]
    player_name = request.form["name"]
    player_age = request.form["age_at_selection"]
    player_salary = request.form[salary_column]
    player_nationality = request.form["nationality"]
    player_iplteam = request.form["ipl_team"]
    player_matches_played = request.form["matches_played"]

    conn = DB2_connection()
    if conn:
        cursor = conn.cursor()
        query = f"""
            INSERT INTO {table_name}(id, name, age_at_selection, {salary_column}, nationality, ipl_team, matches_played)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            player_id, player_name, player_age, player_salary,
            player_nationality, player_iplteam, player_matches_played
        ))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Player record inserted successfully.", "success")
    else:
        flash("Database connection failed.", "error")

    return redirect(url_for("welcome"))

#Updating the players record
@app.route("/update_page", methods=["GET"])
def update_page():
    table_name = get_actual_table_name()
    salary_column = get_salary_column_name(table_name)
    return render_template("update.html", salary_column=salary_column)
@app.route("/update", methods=["POST"])
def update_players():
    table_name = get_actual_table_name()
    salary_column = get_salary_column_name(table_name)

    try:
        player_id = request.form["id"]
        player_name = request.form["name"]
        player_age = request.form["age_at_selection"]
        player_salary = request.form[salary_column]
        player_nationality = request.form["nationality"]
        player_iplteam = request.form["ipl_team"]
        player_matches_played = request.form["matches_played"]
    except KeyError as e:
        flash(f"Missing form field: {e}", "error")
        return redirect(url_for("update_page"))

    conn = DB2_connection()
    if conn:
        cursor = conn.cursor()
        query = f"""
            UPDATE {table_name}
            SET name=%s, age_at_selection=%s, {salary_column}=%s, nationality=%s, ipl_team=%s, matches_played=%s
            WHERE id=%s
        """
        cursor.execute(query, (
            player_name, player_age, player_salary,
            player_nationality, player_iplteam, player_matches_played, player_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Player record updated successfully.", "success")
    else:
        flash("Database connection failed.", "error")

    return redirect(url_for("welcome"))
# Deleting a player record
@app.route("/delete")
def delete_page():
    return render_template("delete.html")
@app.route("/delete_record", methods=["POST"])
def delete_record():
    table_name = get_actual_table_name()
    player_id = request.form["id"]  
    print("Form submitted")
    conn = DB2_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id=%s", (player_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Player deleted successfully.", "success")
    else:
        flash("Failed to connect to database", "error")
    return redirect(url_for("welcome"))
#Viewing the log file
LOG_FILE = "healing_log.txt"
@app.route("/log_view")
def view_log():
    log_contents = "No logs available"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            log_contents = file.read().replace('\r\n', '\n').replace('\r', '\n')
    return render_template("log_view.html", log=log_contents)

if __name__ == "__main__":
    app.run(debug=True)
