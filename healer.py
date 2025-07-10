import requests
import json
from datetime import datetime
import mysql.connector
import re
from db_test_config import DB_CONFIG  # Only DB credentials here
from pymemcache.client.base import Client as MemcacheClient

# 🧠 Detect table name dynamically
def get_actual_table_name():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (DB_CONFIG['database'],)
        )
        tables = cursor.fetchall()
        if not tables:
            raise Exception("❌ No tables found in the database.")
        elif len(tables) == 1:
            return tables[0][0]
        else:
            for table in tables:
                if 'player' in table[0].lower() or 'cricketer' in table[0].lower():
                    return table[0]
            return tables[0][0]
    except Exception as e:
        print(f"❌ Failed to detect table name: {e}")
        return "players"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

TABLE_NAME = get_actual_table_name()

# 🧠 Detect salary column dynamically
def get_salary_column_name():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
        columns = [col[0].lower() for col in cursor.fetchall()]
        keywords = ['salary', 'price', 'compensation', 'pay', 'wage','sal']
        for keyword in keywords:
            for col in columns:
                if keyword in col:
                    return col
        raise Exception("❌ No salary-related column found.")
    except Exception as e:
        print(f"❌ Failed to detect salary column: {e}")
        return "salary_in_cr"  # Fallback
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

SALARY_COLUMN = get_salary_column_name()
print(f"🧠 Detected salary column: {SALARY_COLUMN}")

# 🛠️ Manual Salary Fix
def manually_correct_salary():
    print("🛠️ Manual intervention for negative salaries...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT id, name, {SALARY_COLUMN} FROM {TABLE_NAME} WHERE {SALARY_COLUMN} <= 0"
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("✅ No negative salaries found.")
            return None
        for row in rows:
            print(f"\nPlayer: {row['name']} (ID: {row['id']}) has invalid salary: {row[SALARY_COLUMN]}")
            while True:
                try:
                    new_salary = float(input(f"Enter corrected salary for {row['name']}: "))
                    break
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
            update_query = f"UPDATE {TABLE_NAME} SET {SALARY_COLUMN} = {new_salary} WHERE id = {row['id']}"
            cursor.execute(update_query)
            print(f"✅ Updated salary for {row['name']} to ₹{new_salary} Cr")
        conn.commit()
        print("✅ All corrections applied successfully.")
        return "Manual salary corrections completed."
    except Exception as e:
        print(f"❌ Manual correction failed: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 🤖 Prompt Generator
def call_llama_to_heal(error_msg):
    print("🤖 Sending issue to LLaMA via Ollama...")
    if "Salary should be positive" in error_msg:
        return manually_correct_salary()
    elif "Player names should be unique" in error_msg:
        prompt = f"""
You are a MySQL expert. The '{TABLE_NAME}' table contains duplicate names. Write a SQL DELETE query that removes all duplicates, keeping only the row with the smallest id for each name. Important: Avoid MySQL error 1093 by wrapping the inner SELECT inside another SELECT and aliasing it. Only return the SQL query. No explanation.
Expected Output Format: DELETE FROM {TABLE_NAME} WHERE id NOT IN ( SELECT * FROM ( SELECT MIN(id) FROM {TABLE_NAME} GROUP BY name ) AS temp_ids );
"""
    elif "Nationality should be non null, non empty and set to 'Australian'" in error_msg:
        prompt = f"""
You're a MySQL expert. In the {TABLE_NAME} table:
- Update rows where nationality is NULL, empty, or not 'Australian' (case-insensitive). Set nationality = 'Australian'. Write only a single valid SQL UPDATE query with no explanation.
"""
    elif "IPL Team should be only Chennai Super Kings" in error_msg:
        prompt = f"""
You're a MySQL expert. In the {TABLE_NAME} table, all entries in the ipl_team column must be 'Chennai Super Kings'. Write a single valid SQL UPDATE query that sets ipl_team to 'Chennai Super Kings' if it is NULL or any other team. Do not return any explanation.
"""
    else:
        prompt = f"""
You're a MySQL expert. The {TABLE_NAME} table has a problem. Fix the following issue using a valid SQL UPDATE or DELETE statement. If the SQL fails due to column name mismatch (e.g. '{SALARY_COLUMN}' not found), assume the correct column might be 'salary', 'price', or something similar. ONLY return the corrected SQL query. No explanation. Problem: {error_msg}
"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        })
    )
    suggestion = response.json()['response'].strip()
    with open("healing_log.txt", "a") as log:
        log.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{error_msg}\nSuggested Fix:\n{suggestion}\n{'='*40}\n")
    print("✅ Healing suggestion logged.")
    return suggestion

# 🧪 Datatype fix logic using Memcached
def detect_and_generate_datatype_fix():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {TABLE_NAME}")
        current_columns = cursor.fetchall()
        mem = MemcacheClient(('localhost', 11211))
        mismatches = []
        for col in current_columns:
            col_name, current_type = col[0], col[1]
            cache_key = f"{TABLE_NAME}:{col_name}:type"
            cached_type = mem.get(cache_key)
            if cached_type:
                cached_type = cached_type.decode()
                if current_type.lower() != cached_type.lower():
                    print(f"Datatype mismatch: {col_name}\nCached: {cached_type}\nNow: {current_type}")
                    mismatches.append(f"MODIFY {col_name} {cached_type}")
        if mismatches:
            alter_query = f"ALTER TABLE {TABLE_NAME} " + ", ".join(mismatches) + ";"
            return alter_query
        return None
    except Exception as e:
        print(f"Error checking datatypes: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if 'mem' in locals():
            mem.close()

# 🧹 SQL Cleaner
def clean_sql_query(query):
    query = re.sub(r"sql\n", "", query, flags=re.IGNORECASE).strip()
    lines = query.splitlines()
    sql_lines = []
    for line in lines:
        if re.search(r"\b(update|delete|insert)\b", line, re.IGNORECASE):
            sql_lines.append(line)
        elif sql_lines:
            sql_lines.append(line)
    return "\n".join(sql_lines).strip()

# 🩺 Healing Execution
def heal_sql_query(error_msg, failed_query):
    suggestion = call_llama_to_heal(error_msg)
    if suggestion is None or (isinstance(suggestion, str) and suggestion.startswith("Manual salary corrections")):
        return suggestion
    cleaned_query = clean_sql_query(suggestion)
    if not cleaned_query.lower().startswith(("update", "delete")) or TABLE_NAME.lower() not in cleaned_query.lower():
        print("⚠️ Healing suggestion is not safe or doesn't target the right table. Skipping.")
        return None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("🧪 Attempting to heal the query...")
        cursor.execute(cleaned_query)
        conn.commit()
        print("✅ Healing applied successfully.")
        with open("healing_log.txt", "a") as log:
            log.write(f"Executed SQL:\n{cleaned_query}\n{'='*40}\n")
        return cleaned_query
    except mysql.connector.Error as err:
        print(f"❌ Healing attempt failed: {err}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
