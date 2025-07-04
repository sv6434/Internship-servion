import mysql.connector
import unittest
from db_test_config import DB_CONFIG


class TestDataValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n🔌 Connecting to database for validation tests...")
        try:
            print("Attempting mysql.connector.connect...")
            cls.conn = mysql.connector.connect(**DB_CONFIG)
            print("Connection object created")
            cls.cursor = cls.conn.cursor(dictionary=True)
            print("✅ Connected to DB.")
            cls.cursor.execute("SELECT DATABASE();")
            db_name = cls.cursor.fetchone()['DATABASE()']
            print(f"📌 Connected to Database: {db_name}")
        except Exception as e:
            print("❌ Connection failed:",repr(e))
            raise e

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        print("🔒 Connection closed.\n")

    def test_salary_positive(self):
        """Check all salaries are positive numbers"""
        print("\n🔍 Running test_salary_positive...")
        self.cursor.execute("SELECT * FROM players WHERE salary_in_cr <= 0")
        rows = self.cursor.fetchall()
        print(f"❗ Found {len(rows)} player(s) with salary <= 0: {rows}")
        self.assertEqual(len(rows), 0, "Found players with non-positive salary.")

    
    def test_nationality_not_null(self):
        """Check that nationality is not NULL or empty"""
        print("\n🔍 Running test_nationality_not_null...")
        self.cursor.execute("SELECT * FROM players WHERE nationality IS NULL OR nationality = ''")
        rows = self.cursor.fetchall()
        print(f"❗ Found {len(rows)} player(s) with missing nationality: {rows}")
        self.assertEqual(len(rows), 0, "Found players with missing nationality.")

    def test_unique_names(self):
        """Check that no duplicate names exist"""
        print("\n🔍 Running test_unique_names...")
        self.cursor.execute("""
            SELECT name, COUNT(*) as count FROM players
            GROUP BY name HAVING count > 1
        """)
        rows = self.cursor.fetchall()
        print(f"❗ Found {len(rows)} duplicate name(s): {rows}")
        self.assertEqual(len(rows), 0, "Found duplicate player names.")

    def test_matches_non_negative(self):
        """Check that number of matches played is not negative"""
        print("\n🔍 Running test_matches_non_negative...")
        self.cursor.execute("SELECT * FROM players WHERE matches_played < 0")
        rows = self.cursor.fetchall()
        print(f"❗ Found {len(rows)} player(s) with negative match count: {rows}")
        self.assertEqual(len(rows), 0, "Found players with negative match count.")


if __name__ == '__main__':
    print("🧪 Starting data validation tests...\n")
    unittest.main()
