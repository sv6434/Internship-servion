import requests
import json
from datetime import datetime
import mysql.connector
import re
from db_test_config import DB_CONFIG  # Ensure this file contains correct DB credentials

def call_llama_to_heal(error_msg):
    print("🤖 Sending issue to LLaMA via Ollama...")

    # Use custom prompts for specific errors
    if "Salary should be positive" in error_msg:
        prompt = """
You're a MySQL expert. Some rows in the `players` table have non-positive values in the `salary_in_cr` column.
Write a single valid SQL UPDATE query that sets all salaries ≤ 0 to their absolute value using ABS().
Only output a valid SQL query without explanation.
"""

    elif "Player names should be unique" in error_msg:
        prompt = """
    You are a MySQL expert. The 'players' table contains duplicate names.
    Write a SQL DELETE query that removes all duplicates,**keeping only** the row with the smallest id for each name.
    Important: Avoid MySQL error 1093 by wrapping the inner SELECT inside another SELECT and aliasing it.
    Only return the SQL query. No explanation.

    Expected Output Format:
    DELETE FROM players
    WHERE id NOT IN(
    SELECT * FROM (
    SELECT MIN(id)
    FROM players
    GROUP BY name
    )AS temp_ids
    );
    
   """

    elif "Nationality should be non null, non empty and set to 'Australian'" in error_msg:
        prompt = """
You're a MySQL expert.
In the `players` table where:
-'nationality' is NULL
-OR empty or only spaces
-OR not equal to 'Australian'(case insensitive)

Update only those rows to set 'nationality='Australian''
Write only one valid SQL UPDATE query without any explanation.
"""

    elif "IPL Team should be only Chennai Super Kings" in error_msg:
        prompt = """
You're a MySQL expert. In the `players` table, the `ipl_team` column should only contain the value 'Chennai Super Kings'.
Write a valid SQL UPDATE query that updates all rows where `ipl_team` is NULL or not 'Chennai Super Kings' to 'Chennai Super Kings'.
Only output a valid SQL query without explanation.
"""

    else:
        prompt = f"""
You're a MySQL expert. The `players` table has a problem.
Fix the following issue using a valid SQL UPDATE or DELETE statement.
ONLY return the SQL query. No explanation.

Problem:
{error_msg}
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

def clean_sql_query(query):
    # Remove any explanation or extra lines, keep only the SQL
    query = re.sub(r"```sql|```", "", query, flags=re.IGNORECASE).strip()
    lines = query.splitlines()
    sql_lines = []
    for line in lines:
        if re.search(r"\b(update|delete|insert)\b", line, re.IGNORECASE):
            sql_lines.append(line)
        elif sql_lines:
            sql_lines.append(line)
    return "\n".join(sql_lines).strip()

def heal_sql_query(error_msg, failed_query):
    suggestion = call_llama_to_heal(error_msg)
    cleaned_query = clean_sql_query(suggestion)

    if not cleaned_query.lower().startswith(("update", "delete")) or "players" not in cleaned_query.lower():
        print("⚠️ Healing suggestion is not safe or doesn't target the right table. Skipping.")
        return None

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("🧪 Attempting to heal the query...")
        cursor.execute(cleaned_query)
        conn.commit()
        print("✅ Healing applied successfully.")
        with open("healing_log.txt","a")as log:
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
