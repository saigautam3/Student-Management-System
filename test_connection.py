from database import get_connection

try:
    conn = get_connection()
    print("✅ Connected to PostgreSQL Successfully!")
    conn.close()
except Exception as e:
    print("❌ Connection Failed")
    print(e)