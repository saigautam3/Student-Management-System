import psycopg2
from werkzeug.security import generate_password_hash
from database import get_connection

def run_migration():
    print("Starting database migration for Faculty ERP Authentication features...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Clear child tables referencing users first to avoid constraint issues
        print("- Cleaning dependent records...")
        cur.execute("DELETE FROM student_notes;")
        cur.execute("DELETE FROM notifications;")
        cur.execute("DELETE FROM announcements;")

        # Recreate users table
        print("- Recreating 'users' table...")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                department_id INT REFERENCES departments(id) ON DELETE SET NULL,
                designation VARCHAR(100),
                image_path VARCHAR(255),
                status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Active', 'Rejected', 'Suspended')),
                role VARCHAR(20) DEFAULT 'Faculty' CHECK (role IN ('Admin', 'HOD', 'Faculty')),
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- 'users' table created.")

        # Recreate foreign keys on dependent tables (just to be safe)
        cur.execute("ALTER TABLE student_notes DROP CONSTRAINT IF EXISTS student_notes_faculty_id_fkey;")
        cur.execute("ALTER TABLE student_notes ADD CONSTRAINT student_notes_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES users(id) ON DELETE SET NULL;")
        
        cur.execute("ALTER TABLE announcements DROP CONSTRAINT IF EXISTS announcements_author_id_fkey;")
        cur.execute("ALTER TABLE announcements ADD CONSTRAINT announcements_author_id_fkey FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL;")

        cur.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey;")
        cur.execute("ALTER TABLE notifications ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;")
        print("- Reference constraints restored.")

        # Insert default departments if they don't exist yet
        cur.execute("SELECT COUNT(*) FROM departments")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO departments (name, code, description) VALUES
                ('Computer Science & Engineering', 'CSE', 'Department of Computer Science'),
                ('Electronics & Communication', 'ECE', 'Department of Electronics'),
                ('Mechanical Engineering', 'ME', 'Department of Mechanical');
            """)
            print("- Seeded initial departments.")

        # Get a department ID for default admin
        cur.execute("SELECT id FROM departments LIMIT 1")
        dept_id = cur.fetchone()[0]

        # Insert default active admin user
        hashed_pwd = generate_password_hash('FacultyPass123!')
        cur.execute("""
            INSERT INTO users (username, password_hash, email, full_name, employee_id, department_id, designation, status, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, ('faculty', hashed_pwd, 'admin@university.edu', 'Sai Gautam', 'EMP-001', dept_id, 'Chief Administrator', 'Active', 'Admin'))
        faculty_user_id = cur.fetchone()[0]
        print("- Default faculty admin user ('faculty' / 'FacultyPass123!') created.")

        # Seed other mock users
        hashed_pwd_hod = generate_password_hash('HodPass123!')
        hashed_pwd_fac = generate_password_hash('FacPass123!')
        
        cur.execute("""
            INSERT INTO users (username, password_hash, email, full_name, employee_id, department_id, designation, status, role)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'hod_cse', hashed_pwd_hod, 'hod.cse@university.edu', 'Dr. Rajesh Kumar', 'EMP-002', dept_id, 'Head of Department', 'Active', 'HOD',
            'faculty_john', hashed_pwd_fac, 'john.doe@university.edu', 'John Doe', 'EMP-003', dept_id, 'Assistant Professor', 'Pending', 'Faculty'
        ))
        print("- Seeded mock HOD and pending Faculty users.")

        # Re-verify and clean other tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                details TEXT,
                faculty_username VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_timeline (
                id SERIAL PRIMARY KEY,
                student_id INT REFERENCES students(id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Clean notifications & announcements references to prevent mismatches
        cur.execute("DELETE FROM notifications;")
        cur.execute("DELETE FROM announcements;")

        # Re-seed announcements
        cur.execute("""
            INSERT INTO announcements (title, description, category, priority, author_id)
            VALUES 
            ('Final Examinations Schedule', 'The end-semester examinations will commence from September 1st, 2026. Detailed schedules will be sent shortly.', 'Examination', 'High', %s),
            ('AI & ML Placement Drive', 'Wipro is organizing a recruitment drive for final-year students on August 20th. Registration ends this Friday.', 'Placement', 'High', %s);
        """, (faculty_user_id, faculty_user_id))
        print("- Re-seeded announcements.")

        # Re-seed notifications
        cur.execute("""
            INSERT INTO notifications (user_id, type, message)
            VALUES 
            (%s, 'System Alert', 'Welcome to StudentSphere Faculty ERP Portal! Your administrator role is active.'),
            (%s, 'Announcement', 'New placement drive announcement has been posted.');
        """, (faculty_user_id, faculty_user_id))
        print("- Re-seeded notifications.")

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
