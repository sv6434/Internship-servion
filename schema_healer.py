import mysql.connector
from db_test_config import DB_CONFIG
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
            raise Exception("No tables found in the database.")
        elif len(tables) == 1:
            return tables[0][0]
        else:
            for table in tables:
                if 'player' in table[0].lower() or 'cricketer' in table[0].lower():
                    return table[0]
            return tables[0][0]
    except Exception as e:
        print(f"Failed to detect table name: {e}")
        return "players"
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
#Detect salary column dynamically
def get_salary_column_name(table_name):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [col[0].lower() for col in cursor.fetchall()]
        keywords = ['salary', 'price', 'compensation', 'pay', 'wage', 'sal', 'cost']
        for keyword in keywords:
            for col in columns:
                if keyword in col:
                    return col
        raise Exception("No salary-related column found.")
    except Exception as e:
        print(f"Failed to detect salary column: {e}")
        return "salary_in_cr"
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
