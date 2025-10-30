import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


load_dotenv()

def get_db():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if db.is_connected():
            print("Database connection established.")
            return db

    except Error as e:
        print("Error connecting to MySQL:", e)
        return None
