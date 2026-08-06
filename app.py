from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from database import get_connection, log_activity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import time

app = Flask(__name__)
app.secret_key = "student_management_secret_erp"

# Config uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limits
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Access denied. Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user_record = cur.fetchone()
        cur.close()
        conn.close()
        
        if user_record and check_password_hash(user_record[2], password):
            session['user'] = {
                'id': user_record[0],
                'username': user_record[1]
            }
            log_activity("Admin Login", f"User '{username}' logged in successfully.")
            flash("Welcome back! Logged in successfully.", "success")
            return redirect(url_for('home'))
        else:
            log_activity("Failed Login Attempt", f"Username attempted: '{username}'")
            flash("Invalid username or password.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    if 'user' in session:
        username = session['user']['username']
        session.pop('user', None)
        log_activity("Admin Logout", f"User '{username}' logged out.")
        flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ==========================================
# HOME / READ (DASHBOARD & REGISTRY)
# ==========================================
@app.route("/")
@login_required
def home():
    search = request.args.get("search", "")
    department_filter = request.args.get("department", "")
    status_filter = request.args.get("status", "")
    gpa_min = request.args.get("gpa_min", "")
    gpa_max = request.args.get("gpa_max", "")
    age_filter = request.args.get("age", "")

    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Dashboard Stats ----------------
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM departments")
    total_departments = cur.fetchone()[0]

    cur.execute("SELECT ROUND(AVG(gpa), 2) FROM students")
    avg_gpa_val = cur.fetchone()[0]
    avg_gpa = float(avg_gpa_val) if avg_gpa_val is not None else 0.00

    cur.execute("SELECT COUNT(*) FROM students WHERE status='Active'")
    active_students = cur.fetchone()[0]

    # Additional stats
    cur.execute("SELECT name, gpa FROM students ORDER BY gpa DESC, name LIMIT 1")
    top_perf = cur.fetchone()
    top_performer = f"{top_perf[0]} ({top_perf[1]})" if top_perf else "N/A"

    cur.execute("SELECT name, gpa FROM students ORDER BY gpa ASC, name LIMIT 1")
    low_perf = cur.fetchone()
    lowest_gpa = f"{low_perf[0]} ({low_perf[1]})" if low_perf else "N/A"

    cur.execute("SELECT name FROM students ORDER BY created_at DESC LIMIT 1")
    recent_student = cur.fetchone()
    recently_added = recent_student[0] if recent_student else "N/A"

    cur.execute("SELECT COUNT(*) FROM students WHERE status = 'Inactive'")
    inactive_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM students WHERE status = 'Graduated'")
    graduated_students = cur.fetchone()[0]

    # ---------------- Analytics Charts ----------------
    cur.execute("""
        SELECT d.name, COUNT(s.id), ROUND(COALESCE(AVG(s.gpa), 0), 2)
        FROM departments d
        LEFT JOIN students s ON s.department_id = d.id
        GROUP BY d.id, d.name
        ORDER BY d.name
    """)
    dept_stats = cur.fetchall()

    # GPA Distribution
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN gpa < 5 THEN 1 END) as gpa_0_5,
            COUNT(CASE WHEN gpa >= 5 AND gpa < 7.5 THEN 1 END) as gpa_5_7_5,
            COUNT(CASE WHEN gpa >= 7.5 AND gpa < 8.5 THEN 1 END) as gpa_7_5_8_5,
            COUNT(CASE WHEN gpa >= 8.5 THEN 1 END) as gpa_8_5_10
       FROM students
    """)
    gpa_dist = list(cur.fetchone())

    # Status Distribution
    cur.execute("SELECT status, COUNT(*) FROM students GROUP BY status")
    status_counts = dict(cur.fetchall())
    status_dist = {
        'Active': status_counts.get('Active', 0),
        'Inactive': status_counts.get('Inactive', 0),
        'Graduated': status_counts.get('Graduated', 0)
    }

    # Age Distribution
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN age < 18 THEN 1 END) as age_under_18,
            COUNT(CASE WHEN age >= 18 AND age <= 21 THEN 1 END) as age_18_21,
            COUNT(CASE WHEN age >= 22 AND age <= 25 THEN 1 END) as age_22_25,
            COUNT(CASE WHEN age > 25 THEN 1 END) as age_above_25
        FROM students
    """)
    age_dist = list(cur.fetchone())

    # Monthly Admissions & Growth
    cur.execute("""
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS month, COUNT(*) 
        FROM students 
        GROUP BY month 
        ORDER BY month
    """)
    monthly_data = cur.fetchall()
    months = [row[0] for row in monthly_data]
    monthly_counts = [row[1] for row in monthly_data]
    
    cumulative_counts = []
    total = 0
    for count in monthly_counts:
        total += count
        cumulative_counts.append(total)

    analytics_data = {
        'departments': [row[0] for row in dept_stats],
        'studentCounts': [row[1] for row in dept_stats],
        'avgGpas': [float(row[2]) for row in dept_stats],
        'gpaDist': gpa_dist,
        'statusDist': status_dist,
        'ageDist': age_dist,
        'months': months,
        'monthlyCounts': monthly_counts,
        'cumulativeCounts': cumulative_counts
    }

    # ---------------- Departments for Form / Filter ----------------
    cur.execute("SELECT id, name FROM departments ORDER BY name")
    departments = cur.fetchall()

    # ---------------- Students Records (Filtered) ----------------
    query = """
        SELECT s.id, s.name, s.age, d.name AS department_name, s.email, s.gpa, s.status, s.image_path, s.department_id
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.id
        WHERE s.name ILIKE %s
    """
    values = [f"%{search}%"]
    
    if department_filter:
        query += " AND s.department_id = %s"
        values.append(int(department_filter))
    if status_filter:
        query += " AND s.status = %s"
        values.append(status_filter)
    if gpa_min:
        query += " AND s.gpa >= %s"
        values.append(float(gpa_min))
    if gpa_max:
        query += " AND s.gpa <= %s"
        values.append(float(gpa_max))
    if age_filter:
        query += " AND s.age = %s"
        values.append(int(age_filter))

    query += " ORDER BY s.id"
    cur.execute(query, tuple(values))
    students = cur.fetchall()

    # ---------------- Recent Activity Logs ----------------
    cur.execute("SELECT action, details, created_at FROM activity_logs ORDER BY created_at DESC LIMIT 10")
    activities = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        students=students,
        total_students=total_students,
        total_departments=total_departments,
        avg_gpa=avg_gpa,
        active_students=active_students,
        inactive_students=inactive_students,
        graduated_students=graduated_students,
        top_performer=top_performer,
        lowest_gpa=lowest_gpa,
        recently_added=recently_added,
        dept_stats=dept_stats,
        departments=departments,
        activities=activities,
        analytics_data=analytics_data,
        selected_department=department_filter,
        selected_status=status_filter,
        gpa_min=gpa_min,
        gpa_max=gpa_max,
        age_filter=age_filter,
        search=search
    )

# ==========================================
# STUDENT PROFILE VIEW
# ==========================================
@app.route("/student/<int:id>")
@login_required
def student_profile(id):
    conn = get_connection()
    cur = conn.cursor()
    
    # Get student record
    cur.execute("""
        SELECT s.id, s.name, s.age, d.name AS department_name, s.email, s.gpa, s.status, s.image_path, s.created_at
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.id
        WHERE s.id = %s
    """, (id,))
    student = cur.fetchone()
    
    if not student:
        cur.close()
        conn.close()
        flash("Student profile not found.", "warning")
        return redirect(url_for('home'))

    # Get recent activities related to this student name
    cur.execute("""
        SELECT action, details, created_at 
        FROM activity_logs 
        WHERE details ILIKE %s
        ORDER BY created_at DESC LIMIT 5
    """, (f"%{student[1]}%",))
    student_activities = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("profile.html", student=student, activities=student_activities)

# ==========================================
# ADD STUDENT
# ==========================================
@app.route("/add", methods=["POST"])
@login_required
def add_student():
    name = request.form["name"].strip()
    age = int(request.form["age"])
    department_id = int(request.form["department_id"])
    email = request.form.get("email", "").strip()
    gpa = float(request.form.get("gpa", "0.00"))
    status = request.form.get("status", "Active").strip()

    # Image upload
    image_path = None
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = f"avatar_{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"static/uploads/{filename}"

    conn = get_connection()
    cur = conn.cursor()

    # Check duplicate email
    cur.execute("SELECT COUNT(*) FROM students WHERE email = %s", (email,))
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.close()
        flash(f"Failed to add student. A record with email '{email}' already exists!", "warning")
        return redirect(url_for('home'))

    cur.execute(
        """
        INSERT INTO students
        (name, age, department_id, email, gpa, status, image_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (name, age, department_id, email, gpa, status, image_path)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    log_activity("Student Added", f"Added student: {name} (Email: {email}, GPA: {gpa})")
    flash(f"Student '{name}' added successfully!", "success")
    return redirect(url_for('home'))

# ==========================================
# UPDATE STUDENT
# ==========================================
@app.route("/update/<int:id>", methods=["POST"])
@login_required
def update_student(id):
    name = request.form["name"].strip()
    age = int(request.form["age"])
    department_id = int(request.form["department_id"])
    email = request.form.get("email", "").strip()
    gpa = float(request.form.get("gpa", "0.00"))
    status = request.form.get("status", "Active").strip()

    conn = get_connection()
    cur = conn.cursor()

    # Check duplicate email
    cur.execute("SELECT COUNT(*) FROM students WHERE email = %s AND id != %s", (email, id))
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.close()
        flash(f"Failed to update student. A record with email '{email}' already exists!", "warning")
        return redirect(url_for('home'))

    # Handle image upload
    image_path = None
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = f"avatar_{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"static/uploads/{filename}"

    if image_path:
        cur.execute(
            """
            UPDATE students
            SET name=%s, age=%s, department_id=%s, email=%s, gpa=%s, status=%s, image_path=%s
            WHERE id=%s
            """,
            (name, age, department_id, email, gpa, status, image_path, id)
        )
    else:
        cur.execute(
            """
            UPDATE students
            SET name=%s, age=%s, department_id=%s, email=%s, gpa=%s, status=%s
            WHERE id=%s
            """,
            (name, age, department_id, email, gpa, status, id)
        )

    conn.commit()
    cur.close()
    conn.close()
    
    log_activity("Student Updated", f"Updated student profile: {name} (ID: {id})")
    flash(f"Student '{name}' updated successfully!", "info")
    return redirect(url_for('home'))

# ==========================================
# DELETE STUDENT
# ==========================================
@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    conn = get_connection()
    cur = conn.cursor()
    
    # Get name before deleting for logs
    cur.execute("SELECT name FROM students WHERE id=%s", (id,))
    res = cur.fetchone()
    name = res[0] if res else f"ID: {id}"
    
    cur.execute("DELETE FROM students WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    
    log_activity("Student Deleted", f"Deleted student: {name} (ID: {id})")
    flash("Student deleted successfully!", "danger")
    return redirect(url_for('home'))

# ==========================================
# BULK OPERATIONS ROUTE
# ==========================================
@app.route("/bulk", methods=["POST"])
@login_required
def bulk_operations():
    student_ids = request.form.getlist("student_ids")
    action = request.form.get("action")
    status_val = request.form.get("status_value")

    if not student_ids:
        flash("No students selected for bulk operation.", "warning")
        return redirect(url_for('home'))

    # Parse IDs
    ids = [int(sid) for sid in student_ids]

    conn = get_connection()
    cur = conn.cursor()

    if action == "delete":
        cur.execute("SELECT name FROM students WHERE id = ANY(%s)", (ids,))
        names = ", ".join([row[0] for row in cur.fetchall()])
        cur.execute("DELETE FROM students WHERE id = ANY(%s)", (ids,))
        log_activity("Bulk Student Deletion", f"Deleted students: {names} (IDs: {ids})")
        flash(f"Successfully deleted {len(ids)} students.", "danger")
        
    elif action == "status_update" and status_val:
        cur.execute("UPDATE students SET status = %s WHERE id = ANY(%s)", (status_val, ids))
        log_activity("Bulk Status Update", f"Updated status of student IDs {ids} to '{status_val}'.")
        flash(f"Successfully updated status of {len(ids)} students to {status_val}.", "success")

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

# ==========================================
# DEPARTMENT MANAGEMENT
# ==========================================
@app.route("/departments")
@login_required
def departments_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all departments with their details and aggregated stats
    cur.execute("""
        SELECT d.id, d.name, d.code, d.description, 
               COUNT(s.id) AS student_count, 
               ROUND(COALESCE(AVG(s.gpa), 0), 2) AS avg_gpa
        FROM departments d
        LEFT JOIN students s ON s.department_id = d.id
        GROUP BY d.id, d.name, d.code, d.description
        ORDER BY d.name
    """)
    departments = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("departments.html", departments=departments)

@app.route("/departments/add", methods=["POST"])
@login_required
def add_department():
    name = request.form["name"].strip()
    code = request.form["code"].strip().upper()
    description = request.form.get("description", "").strip()
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO departments (name, code, description)
            VALUES (%s, %s, %s)
        """, (name, code, description))
        conn.commit()
        log_activity("Department Created", f"Created department '{name}' ({code})")
        flash(f"Department '{name}' created successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to create department: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('departments_dashboard'))

@app.route("/departments/edit/<int:id>", methods=["POST"])
@login_required
def edit_department(id):
    name = request.form["name"].strip()
    code = request.form["code"].strip().upper()
    description = request.form.get("description", "").strip()
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE departments
            SET name = %s, code = %s, description = %s
            WHERE id = %s
        """, (name, code, description, id))
        conn.commit()
        log_activity("Department Updated", f"Updated department ID: {id} to '{name}' ({code})")
        flash(f"Department '{name}' updated successfully!", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to update department: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('departments_dashboard'))

@app.route("/departments/delete/<int:id>")
@login_required
def delete_department(id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM departments WHERE id = %s", (id,))
        dept_name = cur.fetchone()[0]
        cur.execute("DELETE FROM departments WHERE id = %s", (id,))
        conn.commit()
        log_activity("Department Deleted", f"Deleted department '{dept_name}' (ID: {id})")
        flash(f"Department '{dept_name}' deleted successfully!", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete department: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('departments_dashboard'))

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)