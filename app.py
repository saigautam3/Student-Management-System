from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from database import get_connection, log_activity, create_notification
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import time
import re

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

# Context processor to inject notifications into all templates
@app.context_processor
def inject_notifications():
    if 'user' in session:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, message, is_read, created_at 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT 15
        """, (session['user']['id'],))
        notifs = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (session['user']['id'],))
        unread_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return dict(notifications=notifs, unread_notifications_count=unread_count)
    return dict(notifications=[], unread_notifications_count=0)

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
            log_activity("Faculty Login", f"User '{username}' logged in successfully.", username)
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
        log_activity("Faculty Logout", f"User '{username}' logged out.", username)
        flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ==========================================
# HOME / READ (DASHBOARD & REGISTRY)
# ==========================================
@app.route("/")
@login_required
def home():
    username = session['user']['username']
    search = request.args.get("search", "")
    department_filter = request.args.get("department", "")
    status_filter = request.args.get("status", "")
    gpa_min = request.args.get("gpa_min", "")
    gpa_max = request.args.get("gpa_max", "")
    age_filter = request.args.get("age", "")
    timeline_filter = request.args.get("timeline_filter", "Today")

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

    # ---------------- AI Academic Insights ----------------
    insights = []
    if total_students > 0:
        # Highest performing dept
        cur.execute("""
            SELECT d.name, ROUND(COALESCE(AVG(s.gpa), 0), 2) AS avg_gpa, COUNT(s.id)
            FROM departments d
            JOIN students s ON s.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY avg_gpa DESC LIMIT 1
        """)
        high_dept = cur.fetchone()
        if high_dept:
            insights.append({
                'title': 'Highest Performing Department',
                'desc': f"{high_dept[0]} leads academically with an average GPA of {high_dept[1]} across {high_dept[2]} students.",
                'icon': 'trending_up',
                'class': 'success'
            })
            
        # Lowest performing dept
        cur.execute("""
            SELECT d.name, ROUND(COALESCE(AVG(s.gpa), 0), 2) AS avg_gpa
            FROM departments d
            JOIN students s ON s.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY avg_gpa ASC LIMIT 1
        """)
        low_dept = cur.fetchone()
        if low_dept and (not high_dept or low_dept[0] != high_dept[0]):
            insights.append({
                'title': 'Targeted Support Needed',
                'desc': f"{low_dept[0]} has the lowest average GPA of {low_dept[1]}. Recommend academic mentoring interventions.",
                'icon': 'announcement',
                'class': 'warning'
            })

        # Max students dept
        cur.execute("""
            SELECT d.name, COUNT(s.id) AS num_students
            FROM departments d
            JOIN students s ON s.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY num_students DESC LIMIT 1
        """)
        max_dept = cur.fetchone()
        if max_dept:
            insights.append({
                'title': 'Department Concentration',
                'desc': f"{max_dept[0]} holds the highest enrollment density with {max_dept[1]} registered student records.",
                'icon': 'groups',
                'class': 'info'
            })

    # ---------------- Risk Prediction Calculations ----------------
    cur.execute("""
        SELECT s.id, s.name, s.gpa, s.status, d.name, s.age 
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.id
        ORDER BY s.gpa ASC
    """)
    all_students_for_risk = cur.fetchall()
    at_risk_list = []
    high_risk_count = 0
    medium_risk_count = 0
    
    for row in all_students_for_risk:
        gpa_val = float(row[2])
        status_val = row[3]
        
        if status_val == 'Inactive':
            level = 'High'
            reason = 'Enrollment status is Inactive'
            high_risk_count += 1
        elif gpa_val < 6.0:
            level = 'High'
            reason = 'Critical GPA (< 6.00)'
            high_risk_count += 1
        elif gpa_val < 7.5:
            level = 'Medium'
            reason = 'Below average GPA (< 7.50)'
            medium_risk_count += 1
        else:
            level = 'Low'
            reason = 'Academic performance stable'
            
        if level in ['High', 'Medium']:
            at_risk_list.append({
                'id': row[0],
                'name': row[1],
                'gpa': gpa_val,
                'status': status_val,
                'department': row[4] or 'Unassigned',
                'level': level,
                'reason': reason
            })
    
    # Sort: High risk first, then lowest GPA first
    at_risk_list.sort(key=lambda x: (0 if x['level'] == 'High' else 1, x['gpa']))

    # ---------------- Department Leaderboard ----------------
    cur.execute("""
        SELECT d.id, d.name, d.code, 
               COUNT(s.id) AS student_count, 
               ROUND(COALESCE(AVG(s.gpa), 0), 2) AS avg_gpa,
               COALESCE(MAX(s.gpa), 0) AS max_gpa
        FROM departments d
        LEFT JOIN students s ON s.department_id = d.id
        GROUP BY d.id, d.name, d.code
        ORDER BY avg_gpa DESC
    """)
    leaderboard = []
    for rank, row in enumerate(cur.fetchall(), 1):
        leaderboard.append({
            'rank': rank,
            'id': row[0],
            'name': row[1],
            'code': row[2],
            'student_count': row[3],
            'avg_gpa': float(row[4]),
            'max_gpa': float(row[5]),
            'score': round((float(row[4]) / 10.00) * 100, 1)
        })

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

    # ---------------- Departments for Filter / Form ----------------
    cur.execute("SELECT id, name FROM departments ORDER BY name")
    departments = cur.fetchall()

    # ---------------- Recent Announcements ----------------
    cur.execute("""
        SELECT a.id, a.title, a.description, a.category, a.priority, a.created_at, u.username
        FROM announcements a
        LEFT JOIN users u ON a.author_id = u.id
        WHERE a.scheduled_date <= CURRENT_TIMESTAMP 
          AND (a.expiry_date IS NULL OR a.expiry_date >= CURRENT_TIMESTAMP)
        ORDER BY a.created_at DESC LIMIT 5
    """)
    announcements_list = cur.fetchall()

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

    # ---------------- Faculty Activity Logs (Filtered) ----------------
    timeline_query = """
        SELECT action, details, created_at, faculty_username 
        FROM activity_logs 
    """
    timeline_vals = []
    if timeline_filter == "Today":
        timeline_query += " WHERE created_at >= CURRENT_DATE"
    elif timeline_filter == "This Week":
        timeline_query += " WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
    elif timeline_filter == "This Month":
        timeline_query += " WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
        
    timeline_query += " ORDER BY created_at DESC LIMIT 30"
    cur.execute(timeline_query, tuple(timeline_vals))
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
        announcements=announcements_list,
        insights=insights,
        at_risk_list=at_risk_list[:5],
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        leaderboard=leaderboard[:3],
        selected_department=department_filter,
        selected_status=status_filter,
        gpa_min=gpa_min,
        gpa_max=gpa_max,
        age_filter=age_filter,
        timeline_filter=timeline_filter,
        search=search
    )

# ==========================================
# STUDENT PROFILE VIEW (WITH NOTES & TIMELINES)
# ==========================================
@app.route("/student/<int:id>")
@login_required
def student_profile(id):
    username = session['user']['username']
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

    # Get private notes
    cur.execute("""
        SELECT n.id, n.note, n.created_at, u.username
        FROM student_notes n
        LEFT JOIN users u ON n.faculty_id = u.id
        WHERE n.student_id = %s
        ORDER BY n.created_at DESC
    """, (id,))
    notes = cur.fetchall()

    # Get chronological timeline events
    cur.execute("""
        SELECT event_type, description, created_at 
        FROM student_timeline 
        WHERE student_id = %s
        ORDER BY created_at DESC
    """, (id,))
    timeline = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Log timeline view action
    log_activity("Profile Viewed", f"Viewed profile of student {student[1]} (ID: {id})", username)
    
    return render_template("profile.html", student=student, notes=notes, timeline=timeline)

# ==========================================
# PRIVATE NOTES ENDPOINTS
# ==========================================
@app.route("/student/<int:id>/notes/add", methods=["POST"])
@login_required
def add_student_note(id):
    username = session['user']['username']
    faculty_id = session['user']['id']
    note_text = request.form["note"].strip()

    if not note_text:
        flash("Cannot save an empty note.", "warning")
        return redirect(url_for('student_profile', id=id))

    conn = get_connection()
    cur = conn.cursor()
    
    # Insert note
    cur.execute("""
        INSERT INTO student_notes (student_id, faculty_id, note)
        VALUES (%s, %s, %s)
    """, (id, faculty_id, note_text))
    
    # Log in student timeline
    cur.execute("""
        INSERT INTO student_timeline (student_id, event_type, description)
        VALUES (%s, 'Faculty Remark', %s)
    """, (id, f"Note added by Faculty '{username}': {note_text[:50]}..."))
    
    conn.commit()
    cur.close()
    conn.close()

    log_activity("Student Note Added", f"Added note to student ID: {id}", username)
    flash("Private note added successfully.", "success")
    return redirect(url_for('student_profile', id=id))

@app.route("/student/<int:sid>/notes/delete/<int:nid>")
@login_required
def delete_student_note(sid, nid):
    username = session['user']['username']
    conn = get_connection()
    cur = conn.cursor()
    
    # Delete note
    cur.execute("DELETE FROM student_notes WHERE id = %s AND student_id = %s", (nid, sid))
    
    # Log timeline
    cur.execute("""
        INSERT INTO student_timeline (student_id, event_type, description)
        VALUES (%s, 'Profile Modification', %s)
    """, (sid, f"Faculty note deleted by '{username}'"))
    
    conn.commit()
    cur.close()
    conn.close()

    log_activity("Student Note Deleted", f"Deleted note ID {nid} for student ID {sid}", username)
    flash("Private note deleted.", "info")
    return redirect(url_for('student_profile', id=sid))

# ==========================================
# ADD STUDENT (WITH AUTO TIMELINE)
# ==========================================
@app.route("/add", methods=["POST"])
@login_required
def add_student():
    username = session['user']['username']
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

    # Insert student
    cur.execute(
        """
        INSERT INTO students
        (name, age, department_id, email, gpa, status, image_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (name, age, department_id, email, gpa, status, image_path)
    )
    new_id = cur.fetchone()[0]

    # Create timeline entry
    cur.execute("""
        INSERT INTO student_timeline (student_id, event_type, description)
        VALUES (%s, 'Admission', %s)
    """, (new_id, f"Admitted to university with status '{status}' and initial GPA of {gpa}"))

    conn.commit()
    
    # Fetch all faculty to notify
    cur.execute("SELECT id FROM users")
    faculty_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    # Create notification alerts for all faculty
    for fid in faculty_ids:
        create_notification(fid, 'Student Alert', f"New student registered: {name} (Dept ID: {department_id})")

    log_activity("Student Added", f"Added student: {name} (Email: {email}, GPA: {gpa})", username)
    flash(f"Student '{name}' added successfully!", "success")
    return redirect(url_for('home'))

# ==========================================
# UPDATE STUDENT (WITH AUTO TIMELINE)
# ==========================================
@app.route("/update/<int:id>", methods=["POST"])
@login_required
def update_student(id):
    username = session['user']['username']
    name = request.form["name"].strip()
    age = int(request.form["age"])
    department_id = int(request.form["department_id"])
    email = request.form.get("email", "").strip()
    gpa = float(request.form.get("gpa", "0.00"))
    status = request.form.get("status", "Active").strip()

    conn = get_connection()
    cur = conn.cursor()

    # Get old details to log differences in timeline
    cur.execute("SELECT name, age, department_id, email, gpa, status FROM students WHERE id = %s", (id,))
    old = cur.fetchone()
    
    if not old:
        cur.close()
        conn.close()
        flash("Student not found.", "warning")
        return redirect(url_for('home'))

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

    # Log changes into student academic timeline
    if old[0] != name:
        cur.execute("INSERT INTO student_timeline (student_id, event_type, description) VALUES (%s, 'Profile Modification', %s)", (id, f"Name changed from '{old[0]}' to '{name}'"))
    if old[2] != department_id:
        cur.execute("SELECT name FROM departments WHERE id = %s", (department_id,))
        new_dept_name = cur.fetchone()[0]
        cur.execute("INSERT INTO student_timeline (student_id, event_type, description) VALUES (%s, 'Department Change', %s)", (id, f"Transferred department to '{new_dept_name}'"))
    if float(old[4]) != gpa:
        cur.execute("INSERT INTO student_timeline (student_id, event_type, description) VALUES (%s, 'GPA Update', %s)", (id, f"GPA altered from {old[4]} to {gpa}"))
    if old[5] != status:
        cur.execute("INSERT INTO student_timeline (student_id, event_type, description) VALUES (%s, 'Status Update', %s)", (id, f"Enrollment status changed from '{old[5]}' to '{status}'"))

    conn.commit()
    cur.close()
    conn.close()
    
    log_activity("Student Updated", f"Updated student profile: {name} (ID: {id})", username)
    flash(f"Student '{name}' updated successfully!", "info")
    return redirect(url_for('home'))

# ==========================================
# DELETE STUDENT
# ==========================================
@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    username = session['user']['username']
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
    
    log_activity("Student Deleted", f"Deleted student: {name} (ID: {id})", username)
    flash("Student deleted successfully!", "danger")
    return redirect(url_for('home'))

# ==========================================
# BULK OPERATIONS ROUTE
# ==========================================
@app.route("/bulk", methods=["POST"])
@login_required
def bulk_operations():
    username = session['user']['username']
    student_ids = request.form.getlist("student_ids")
    action = request.form.get("action")
    status_val = request.form.get("status_value")

    if not student_ids:
        flash("No students selected for bulk operation.", "warning")
        return redirect(url_for('home'))

    ids = [int(sid) for sid in student_ids]
    conn = get_connection()
    cur = conn.cursor()

    if action == "delete":
        cur.execute("SELECT name FROM students WHERE id = ANY(%s)", (ids,))
        names = ", ".join([row[0] for row in cur.fetchall()])
        cur.execute("DELETE FROM students WHERE id = ANY(%s)", (ids,))
        log_activity("Bulk Student Deletion", f"Deleted students: {names} (IDs: {ids})", username)
        flash(f"Successfully deleted {len(ids)} students.", "danger")
        
    elif action == "status_update" and status_val:
        cur.execute("UPDATE students SET status = %s WHERE id = ANY(%s)", (status_val, ids))
        # Log timeline events for updated students
        for sid in ids:
            cur.execute("INSERT INTO student_timeline (student_id, event_type, description) VALUES (%s, 'Status Update', %s)", (sid, f"Status updated via bulk action to '{status_val}'"))
        conn.commit()
        log_activity("Bulk Status Update", f"Updated status of student IDs {ids} to '{status_val}'.", username)
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
    username = session['user']['username']
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
        log_activity("Department Created", f"Created department '{name}' ({code})", username)
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
    username = session['user']['username']
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
        log_activity("Department Updated", f"Updated department ID: {id} to '{name}' ({code})", username)
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
    username = session['user']['username']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM departments WHERE id = %s", (id,))
        dept_name = cur.fetchone()[0]
        cur.execute("DELETE FROM departments WHERE id = %s", (id,))
        conn.commit()
        log_activity("Department Deleted", f"Deleted department '{dept_name}' (ID: {id})", username)
        flash(f"Department '{dept_name}' deleted successfully!", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete department: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('departments_dashboard'))

# ==========================================
# FACULTY ANNOUNCEMENTS HUB
# ==========================================
@app.route("/announcements")
@login_required
def announcements_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    
    # Query all announcements
    cur.execute("""
        SELECT a.id, a.title, a.description, a.category, a.priority, a.created_at, a.expiry_date, u.username, a.scheduled_date
        FROM announcements a
        LEFT JOIN users u ON a.author_id = u.id
        ORDER BY a.created_at DESC
    """)
    announcements = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("announcements.html", announcements=announcements)

@app.route("/announcements/add", methods=["POST"])
@login_required
def add_announcement():
    username = session['user']['username']
    author_id = session['user']['id']
    title = request.form["title"].strip()
    description = request.form["description"].strip()
    category = request.form["category"].strip()
    priority = request.form["priority"].strip()
    scheduled_val = request.form.get("scheduled_date", "")
    expiry_val = request.form.get("expiry_date", "")

    # Set formats
    scheduled_date = scheduled_val if scheduled_val else None
    expiry_date = expiry_val if expiry_val else None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO announcements (title, description, category, priority, scheduled_date, expiry_date, author_id)
            VALUES (%s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), %s, %s)
            RETURNING id;
        """, (title, description, category, priority, scheduled_date, expiry_date, author_id))
        conn.commit()
        
        # Notify all faculty
        cur.execute("SELECT id FROM users")
        faculty_ids = [row[0] for row in cur.fetchall()]
        for fid in faculty_ids:
            create_notification(fid, 'Announcement', f"New announcement posted: {title} ({category})")
            
        log_activity("Announcement Created", f"Posted announcement: {title}", username)
        flash("Announcement published successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to post announcement: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('announcements_dashboard'))

@app.route("/announcements/delete/<int:id>")
@login_required
def delete_announcement(id):
    username = session['user']['username']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM announcements WHERE id = %s", (id,))
        conn.commit()
        log_activity("Announcement Deleted", f"Deleted announcement ID: {id}", username)
        flash("Announcement removed successfully.", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete announcement: {str(e)}", "danger")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('announcements_dashboard'))

# ==========================================
# SYSTEM NOTIFICATIONS ENDPOINTS
# ==========================================
@app.route("/notifications/mark-read/<int:id>", methods=["POST"])
@login_required
def mark_notification_read(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s", (id, session['user']['id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'success'})

@app.route("/notifications/clear-all", methods=["POST"])
@login_required
def clear_all_notifications():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notifications WHERE user_id = %s", (session['user']['id'],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'success'})

# ==========================================
# PROFESSIONAL REPORTS HUB
# ==========================================
@app.route("/reports")
@login_required
def reports_hub():
    username = session['user']['username']
    conn = get_connection()
    cur = conn.cursor()
    
    # Compute aggregations for report
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM students WHERE status = 'Active'")
    active_students = cur.fetchone()[0]
    
    cur.execute("SELECT ROUND(AVG(gpa), 2) FROM students")
    avg_gpa_val = cur.fetchone()[0]
    avg_gpa = float(avg_gpa_val) if avg_gpa_val is not None else 0.00

    # Fetch departments detailed stats for reporting
    cur.execute("""
        SELECT d.name, d.code, COUNT(s.id) AS student_count, 
               ROUND(COALESCE(AVG(s.gpa), 0), 2) AS avg_gpa
        FROM departments d
        LEFT JOIN students s ON s.department_id = d.id
        GROUP BY d.id, d.name, d.code
        ORDER BY d.name
    """)
    departments = cur.fetchall()

    # Fetch student lists for report table
    cur.execute("""
        SELECT s.id, s.name, s.email, d.name, s.gpa, s.status, s.age
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.id
        ORDER BY d.name, s.name
    """)
    students = cur.fetchall()
    
    cur.close()
    conn.close()
    
    log_activity("Report Generated", "Compiled academic summary report.", username)
    
    return render_template("reports.html", 
                           total_students=total_students, 
                           active_students=active_students, 
                           avg_gpa=avg_gpa, 
                           departments=departments, 
                           students=students,
                           faculty_name=username,
                           current_date=time.strftime('%B %d, %Y'))

# ==========================================
# ACCOUNT SETTINGS
# ==========================================
import re

def is_secure_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[@$!%*?&#]", password):
        return False, "Password must contain at least one special character (@$!%*?&#)."
    return True, ""

def is_secure_username(username):
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not re.match(r"^[a-zA-Z0-9_\-]+$", username):
        return False, "Username can only contain alphanumeric characters, underscores, and hyphens."
    return True, ""

@app.route("/settings")
@login_required
def settings_page():
    username = session['user']['username']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, email FROM users WHERE username = %s", (username,))
    user_info = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("settings.html", user_info=user_info)

@app.route("/settings/update-profile", methods=["POST"])
@login_required
def update_profile():
    new_username = request.form["username"].strip()
    new_email = request.form.get("email", "").strip()
    
    # Validate username
    is_valid, error_msg = is_secure_username(new_username)
    if not is_valid:
        flash(error_msg, "danger")
        return redirect(url_for('settings_page'))
        
    current_id = session['user']['id']
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Check duplicate username
    cur.execute("SELECT COUNT(*) FROM users WHERE username = %s AND id != %s", (new_username, current_id))
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.close()
        flash(f"Username '{new_username}' is already taken.", "danger")
        return redirect(url_for('settings_page'))
        
    # Update
    cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (new_username, new_email, current_id))
    conn.commit()
    cur.close()
    conn.close()
    
    # Update session
    session['user']['username'] = new_username
    
    log_activity("Faculty Profile Updated", f"User ID {current_id} changed username to '{new_username}'.", new_username)
    flash("Profile updated successfully!", "success")
    return redirect(url_for('settings_page'))

@app.route("/settings/change-password", methods=["POST"])
@login_required
def change_password():
    username = session['user']['username']
    current_password = request.form["current_password"].strip()
    new_password = request.form["new_password"].strip()
    confirm_password = request.form["confirm_password"].strip()

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('settings_page'))

    # Validate secure password rules
    is_valid, error_msg = is_secure_password(new_password)
    if not is_valid:
        flash(error_msg, "danger")
        return redirect(url_for('settings_page'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    record = cur.fetchone()
    
    if not record or not check_password_hash(record[0], current_password):
        cur.close()
        conn.close()
        flash("Incorrect current password.", "danger")
        return redirect(url_for('settings_page'))

    # Update to new password
    new_password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password_hash = %s WHERE username = %s", (new_password_hash, username))
    conn.commit()
    cur.close()
    conn.close()

    log_activity("Password Changed", f"User '{username}' changed their password.", username)
    flash("Password updated successfully!", "success")
    return redirect(url_for('settings_page'))

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)