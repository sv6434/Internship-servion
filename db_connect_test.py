import mysql.connector
from db_test_config import DB_CONFIG
try:
    print("Trying to connect...")
    conn=mysql.connector.connect(**DB_CONFIG)
    print("Connection successfull")
    conn.close()
except Exception as e:
    print("Connection failed:",e)
