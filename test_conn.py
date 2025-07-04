import mysql.connector
try:
    print("Connecting")
    conn=mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Sashtarun01@",
        database="csk_players_db"
    )
    print("Connected to MySQL!")
    conn.close()
except Exception as e:
    print("Failed:",repr(e))
    
