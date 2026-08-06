import psycopg2
from werkzeug.security import generate_password_hash
from database import get_connection

def run_migration():
    print("Starting database migration...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1. Create users table for authentication
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'users' table created or already exists.")

        # 2. Insert default admin user if none exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            hashed_pwd = generate_password_hash('adminpassword')
            cur.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, ('admin', hashed_pwd, 'admin@university.edu'))
            print("- Default admin user ('admin' / 'adminpassword') created.")
        else:
            print("- Default admin user already exists.")

        # 3. Create departments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'departments' table created or already exists.")

        # 4. Create activity_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'activity_logs' table created or already exists.")

        # 5. Check students table and add new columns if missing
        # Add created_at column
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'students' AND column_name = 'created_at';
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE students ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            print("- Column 'created_at' added to 'students' table.")

        # Add image_path column
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'students' AND column_name = 'image_path';
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE students ADD COLUMN image_path VARCHAR(255);")
            print("- Column 'image_path' added to 'students' table.")

        # Add department_id column
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'students' AND column_name = 'department_id';
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE students ADD COLUMN department_id INT REFERENCES departments(id) ON DELETE SET NULL;")
            print("- Column 'department_id' added to 'students' table.")

        # 6. Migrate existing department text data to departments table
        # Check if the text department column exists in students table
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'students' AND column_name = 'department';
        """)
        if cur.fetchone():
            print("Migrating departments string values to the normalized table...")
            cur.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL AND department != '';")
            existing_depts = [row[0] for row in cur.fetchall()]

            for dept_name in existing_depts:
                # Generate a code like CSE, CSM, CSD or similar
                code = dept_name.strip().upper()[:20]
                cur.execute("SELECT id FROM departments WHERE name = %s OR code = %s", (dept_name, code))
                exists = cur.fetchone()
                if not exists:
                    cur.execute("""
                        INSERT INTO departments (name, code, description)
                        VALUES (%s, %s, %s)
                        RETURNING id;
                    """, (dept_name, code, f"{dept_name} Department"))
                    dept_id = cur.fetchone()[0]
                else:
                    dept_id = exists[0]

                # Update students with this department_id
                cur.execute("""
                    UPDATE students SET department_id = %s
                    WHERE department = %s;
                """, (dept_id, dept_name))
            
            # Now drop the old text column
            cur.execute("ALTER TABLE students DROP COLUMN department;")
            print("- Migration complete: text 'department' column dropped and data normalized.")

        # 7. Update status check constraint (Active, Inactive, Graduated)
        # Drop existing constraint if any, and create a new check constraint
        # To be safe, we can try dropping potential constraints, or just run a try/catch to add check constraint
        try:
            cur.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS students_status_check;")
            cur.execute("ALTER TABLE students ADD CONSTRAINT students_status_check CHECK (status IN ('Active', 'Inactive', 'Graduated'));")
            print("- Status check constraint updated to allow ('Active', 'Inactive', 'Graduated').")
        except Exception as ec:
            print("- Skipping constraint alteration (already matches or different name):", ec)

        conn.commit()
        print("Database migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print("Error during database migration:")
        print(e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
