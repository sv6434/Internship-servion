import mysql.connector
from pymemcache.client import base
from db_test_config import DB_CONFIG
#Dynamically get the table name
def get_table_name():
    try:
        conn=mysql.connector.connect(**DB_CONFIG)
        cursor=conn.cursor()
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s",
            (DB_CONFIG['database'],)
        )
        tables=cursor.fetchall()
        if not tables:
            raise Exception("No tables found in the database.")
        elif len(tables)==1:
            return tables[0][0]
        else:
            for table in tables:
                if 'player' in table[0].lower():
                    return table[0]
            return tables[0][0]
    except Exception as e:
        print(f"Error: {e}")
        return "players"
    finally:
        if 'cursor' in locals():cursor.close()
        if 'conn' in locals():conn.close()
#Catch the column datatypes using pymemcache
def cache_column_datatypes():
    table_name=get_table_name()
    print(f"Catching datatypes for table:{table_name}")
    try:
        conn=mysql.connector.connect(**DB_CONFIG)
        cursor=conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns=cursor.fetchall()
        client=base.Client(('localhost',11211))
        for col in columns:
            col_name,col_type=col[0],col[1]
            key=f"{table_name}:{col_name}:type"
            client.set(key,col_type)
            print(f"Cached {key}={col_type}")
    except Exception as e:
        print(f"Failed to cache column types: {e}")
    finally:
        if 'cursor' in locals():cursor.close()
        if 'conn' in locals(): conn.close()
if __name__=="__main__":
    cache_column_datatypes()
    
        
