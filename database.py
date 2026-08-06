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

def log_activity(action, details=None, faculty_username=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activity_logs (action, details, faculty_username) VALUES (%s, %s, %s)",
            (action, details, faculty_username)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error logging activity:", e)

def create_notification(user_id, type_str, message_str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notifications (user_id, type, message) VALUES (%s, %s, %s)",
            (user_id, type_str, message_str)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error creating notification:", e)


#import os
#import psycopg2
#def get_connection():

#    conn = psycopg2.connect(
#       host=os.environ.get("dpg-d9bt8crbc2fs73b1dj50-a"),
#        database=os.environ.get("studentdb_cle3"),
#        user=os.environ.get("studentdb_cle3_user"),
#        password=os.environ.get("root"),
#        port=os.environ.get("5432")
#    )
#    return conn