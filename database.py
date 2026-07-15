import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="studentdb",
        user="postgres",
        password="root",
        port="5432"
    )
    return conn