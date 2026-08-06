import psycopg2
from werkzeug.security import generate_password_hash
from database import get_connection

def run_migration():
    print("Starting database migration for Faculty ERP features...")
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
        print("- 'users' table checked.")

        # 2. Insert default faculty user if none exists
        cur.execute("SELECT id FROM users WHERE username = 'faculty'")
        user_record = cur.fetchone()
        if not user_record:
            hashed_pwd = generate_password_hash('FacultyPass123!')
            cur.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, ('faculty', hashed_pwd, 'faculty@university.edu'))
            faculty_user_id = cur.fetchone()[0]
            print("- Default faculty user ('faculty' / 'FacultyPass123!') created.")
        else:
            faculty_user_id = user_record[0]
            print("- Default faculty user already exists.")

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
        print("- 'departments' table checked.")

        # 4. Create activity_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'activity_logs' table checked.")

        # Add faculty_username column if missing
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'activity_logs' AND column_name = 'faculty_username';
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE activity_logs ADD COLUMN faculty_username VARCHAR(50);")
            print("- Column 'faculty_username' added to 'activity_logs' table.")

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

                cur.execute("""
                    UPDATE students SET department_id = %s
                    WHERE department = %s;
                """, (dept_id, dept_name))
            
            cur.execute("ALTER TABLE students DROP COLUMN department;")
            print("- Migration complete: text 'department' column dropped.")

        # 7. Update status check constraint (Active, Inactive, Graduated)
        try:
            cur.execute("ALTER TABLE students DROP CONSTRAINT IF EXISTS students_status_check;")
            cur.execute("ALTER TABLE students ADD CONSTRAINT students_status_check CHECK (status IN ('Active', 'Inactive', 'Graduated'));")
            print("- Status check constraint updated.")
        except Exception as ec:
            print("- Skipping constraint alteration:", ec)

        # 8. Create new tables for ERP features
        # student_notes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_notes (
                id SERIAL PRIMARY KEY,
                student_id INT REFERENCES students(id) ON DELETE CASCADE,
                faculty_id INT REFERENCES users(id) ON DELETE SET NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'student_notes' table checked.")

        # student_timeline
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_timeline (
                id SERIAL PRIMARY KEY,
                student_id INT REFERENCES students(id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'student_timeline' table checked.")

        # announcements
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(150) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                scheduled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP,
                author_id INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'announcements' table checked.")

        # notifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'notifications' table checked.")

        # 9. Seed Mock/Demo Data
        # Seed announcements
        cur.execute("SELECT COUNT(*) FROM announcements")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO announcements (title, description, category, priority, author_id)
                VALUES 
                ('Final Examinations Schedule', 'The end-semester examinations will commence from September 1st, 2026. Detailed schedules will be sent shortly.', 'Examination', 'High', %s),
                ('AI & ML Placement Drive', 'Wipro is organizing a recruitment drive for final-year students on August 20th. Registration ends this Friday.', 'Placement', 'High', %s),
                ('Annual Tech Symposium', 'Call for paper submission and prototype exhibitions for the upcoming TechVeda 2026 symposium is now open.', 'Workshop', 'Medium', %s);
            """, (faculty_user_id, faculty_user_id, faculty_user_id))
            print("- Seeded initial mock announcements.")

        # Seed notifications
        cur.execute("SELECT COUNT(*) FROM notifications")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO notifications (user_id, type, message)
                VALUES 
                (%s, 'System Alert', 'Welcome to StudentSphere Faculty ERP Portal! Check your settings to customize your account.'),
                (%s, 'Announcement', 'New placement drive announcement has been posted: AI & ML Placement Drive.');
            """, (faculty_user_id, faculty_user_id))
            print("- Seeded initial mock notifications.")

        # Seed timeline and notes for existing students
        cur.execute("SELECT id, name, gpa FROM students")
        students_list = cur.fetchall()
        for student in students_list:
            sid, name, gpa = student
            
            # Seed admission event in timeline if none exists
            cur.execute("SELECT COUNT(*) FROM student_timeline WHERE student_id = %s", (sid,))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO student_timeline (student_id, event_type, description)
                    VALUES (%s, 'Admission', %s)
                """, (sid, f"Student {name} registered in system with initial GPA of {gpa}"))
                
            # Seed initial notes if none exists
            cur.execute("SELECT COUNT(*) FROM student_notes WHERE student_id = %s", (sid,))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO student_notes (student_id, faculty_id, note)
                    VALUES (%s, %s, %s)
                """, (sid, faculty_user_id, "Demonstrates consistent performance. Advised to participate in upcoming workshops."))

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
