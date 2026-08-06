import psycopg2
from database import get_connection

def run_enterprise_migration():
    print("Starting database migration for StudentSphere Enterprise Modules...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Create academic_events table
        print("- Creating 'academic_events' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS academic_events (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                event_type VARCHAR(50) NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                color_code VARCHAR(10) DEFAULT '#3b82f6',
                faculty_id INT REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create student_imports table
        print("- Creating 'student_imports' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_imports (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                imported_count INT DEFAULT 0,
                skipped_count INT DEFAULT 0,
                failed_count INT DEFAULT 0,
                faculty_id INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create student_import_errors table
        print("- Creating 'student_import_errors' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_import_errors (
                id SERIAL PRIMARY KEY,
                import_id INT REFERENCES student_imports(id) ON DELETE CASCADE,
                row_number INT,
                student_name VARCHAR(100),
                email VARCHAR(150),
                reason TEXT,
                status VARCHAR(20)
            );
        """)

        # Create attendance_sessions table
        print("- Creating 'attendance_sessions' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id SERIAL PRIMARY KEY,
                department_id INT REFERENCES departments(id) ON DELETE CASCADE,
                session_date DATE NOT NULL,
                lecture_topic VARCHAR(200) NOT NULL,
                faculty_id INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_session UNIQUE (department_id, session_date, lecture_topic)
            );
        """)

        # Create attendance_records table
        print("- Creating 'attendance_records' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id SERIAL PRIMARY KEY,
                session_id INT REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                student_id INT REFERENCES students(id) ON DELETE CASCADE,
                status VARCHAR(10) NOT NULL CHECK (status IN ('Present', 'Absent')),
                CONSTRAINT unique_attendance UNIQUE (session_id, student_id)
            );
        """)

        # Create student_marks table
        print("- Creating 'student_marks' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_marks (
                id SERIAL PRIMARY KEY,
                student_id INT REFERENCES students(id) ON DELETE CASCADE UNIQUE,
                internal_marks NUMERIC(5, 2) DEFAULT 0.00 CHECK (internal_marks >= 0.00 AND internal_marks <= 20.00),
                lab_marks NUMERIC(5, 2) DEFAULT 0.00 CHECK (lab_marks >= 0.00 AND lab_marks <= 20.00),
                mid_marks NUMERIC(5, 2) DEFAULT 0.00 CHECK (mid_marks >= 0.00 AND mid_marks <= 30.00),
                final_marks NUMERIC(5, 2) DEFAULT 0.00 CHECK (final_marks >= 0.00 AND final_marks <= 100.00),
                total_marks NUMERIC(5, 2) DEFAULT 0.00,
                percentage NUMERIC(5, 2) DEFAULT 0.00,
                gpa NUMERIC(4, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("Enterprise database migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print("Error during database migration:")
        print(e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_enterprise_migration()
