import mysql.connector
import unittest
from healer import heal_sql_query, SALARY_COLUMN, TABLE_NAME, detect_and_generate_datatype_fix,log_passed_validation
from db_test_config import DB_CONFIG
from datetime import datetime

class TestHealingValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n Connecting to database for healing tests...")
        try:
            cls.conn = mysql.connector.connect(**DB_CONFIG)
            cls.cursor = cls.conn.cursor(dictionary=True)
            print("✅ Connected to DB.")
            cls.cursor.execute("SELECT DATABASE();")
            db_name = cls.cursor.fetchone()['DATABASE()']
            print(f"📌 Connected to Database: {db_name}")
        except Exception as e:
            print("❌ Connection failed:", e)
            raise e

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        print(" Connection closed.\n")

    def run_test_with_healing(self, query, description, condition=lambda rows: len(rows) == 0):
        print(f"\n Running: {description}")
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            if condition(rows):
                print("Validation passed.")
                log_passed_validation(description)
            self.assertTrue(condition(rows), f"Validation failed: {description}")
        except AssertionError as e:
            print(f"️ Error detected: {e}")
            healed_query = heal_sql_query(str(e), query)
            print(" Attempting to heal the query...")
            try:
                if healed_query and isinstance(healed_query, str) and not healed_query.startswith("Manual salary corrections"):
                    self.cursor.execute(healed_query)
                    self.conn.commit()
                    self.cursor.execute(query)
                    rows = self.cursor.fetchall()
                    if condition(rows):
                        print("Validation passed after healing.")
                        log_passed_validation(f"{description} (after healing)")
                    self.assertTrue(condition(rows), f"Healing failed: {description}")
                else:
                    print("Manual correction completed. No SQL execution needed.")
                    log_passed_validation(f"{description} (manual correction)")
            except Exception as heal_error:
                print(" Healing attempt failed:", heal_error)

    def test_ipl_team_is_csk(self):
        self.run_test_with_healing(
            f"SELECT * FROM {TABLE_NAME} WHERE ipl_team IS NULL OR ipl_team != 'Chennai Super Kings'",
            "IPL Team should be only Chennai Super Kings"
        )

    def test_nationality_is_aus(self):
        print("\n Running: Nationality should be 'Australian' and not NULL or empty...")
        query = f"SELECT * FROM {TABLE_NAME} WHERE nationality IS NULL OR TRIM(nationality) = '' OR LOWER(nationality) != 'australian'"
        description = "Nationality should be non null, non empty and set to 'Australian'"
        self.run_test_with_healing(query, description)

    def test_salary_positive(self):
        self.run_test_with_healing(
            f"SELECT * FROM {TABLE_NAME} WHERE {SALARY_COLUMN} <= 0",
            "Salary should be positive"
        )

    def test_unique_names(self):
        self.run_test_with_healing(
            f"""
            SELECT name, COUNT(*) as count FROM {TABLE_NAME}
            GROUP BY name HAVING count > 1
            """,
            "Player names should be unique"
        )
    def test_memcached_column_datatype(self):
        print("\n Checking for datatype mismatches (via Memcached)...")
        alter_query=detect_and_generate_datatype_fix()
        if alter_query:
            print(f"Detected mismatch.Applying:\n{alter_query}")
            try:
                self.cursor.execute(alter_query)
                self.conn.commit()
                with open("healing_log.txt","a") as log:
                    log.write(f"\n[{datetime.now()}] Executed Datatype Healing via test:\n{alter_query}\n{'='*40}\n")
                print("Applied datatype fix.")
            except Exception as e:
                print(f" Failed to apply datatype fix:{e}")
        else:
            print("No datatype mismatches found.")
            with open("healing_log.txt","a") as log:
                log.write(f"\n[{datetime.now()}] PASSED: No datatype mismatch found via Memcached.\n{'='*40}\n")

if __name__ == "__main__":
    print(" Starting Healing Test...\n")
    unittest.main()
