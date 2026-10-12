def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "blood_donation_db"),
        port=int(os.getenv("DB_PORT", "3306"))
    )
try:
    db = get_db_connection()
    print("Database connected successfully!")
    db.close()
except Exception as e:
    print("Database connection failed:", e)import os
import mysql.connector

