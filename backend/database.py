import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


load_dotenv()

def get_db():
    try:
        # Use 127.0.0.1 instead of localhost to force TCP/IP connection on Windows
        host = os.getenv("DB_HOST", "localhost")
        if host == "localhost":
            host = "127.0.0.1"
        
        db = mysql.connector.connect(
            host=host,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=3306,
            use_unicode=True,
            charset='utf8mb4'
        )

        if db.is_connected():
            print("Database connection established.")
            return db

    except Error as e:
        print("Error connecting to MySQL:", e)
        return None
