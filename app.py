from flask import Flask, render_template, request, redirect, flash
from database import get_connection

app = Flask(__name__)
app.secret_key = "student_management_secret"

# ==========================================
# HOME / READ
# ==========================================
@app.route("/")
def home():
    search = request.args.get("search", "")
    department = request.args.get("department", "")
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Dashboard Stats ----------------
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT department) FROM students")
    total_departments = cur.fetchone()[0]

    cur.execute("SELECT ROUND(AVG(gpa), 2) FROM students")
    avg_gpa_val = cur.fetchone()[0]
    avg_gpa = float(avg_gpa_val) if avg_gpa_val is not None else 0.00

    cur.execute("SELECT COUNT(*) FROM students WHERE status='Active'")
    active_students = cur.fetchone()[0]

    # ---------------- Department stats for Chart.js ----------------
    cur.execute("""
        SELECT department, COUNT(*), ROUND(AVG(gpa), 2)
        FROM students
        GROUP BY department
        ORDER BY department
    """)
    dept_stats = cur.fetchall()

    # ---------------- Departments List for Filter ----------------
    cur.execute("""
        SELECT DISTINCT department
        FROM students
        ORDER BY department
    """)
    departments = cur.fetchall()

    # ---------------- Students Records ----------------
    query = """
        SELECT id, name, age, department, email, gpa, status
        FROM students
        WHERE name ILIKE %s
    """
    values = [f"%{search}%"]
    if department:
        query += " AND department=%s"
        values.append(department)
    query += " ORDER BY id"
    cur.execute(query, tuple(values))
    students = cur.fetchall()

    cur.close()
    conn.close()
    return render_template(
        "index.html",
        students=students,
        total_students=total_students,
        total_departments=total_departments,
        avg_gpa=avg_gpa,
        active_students=active_students,
        dept_stats=dept_stats,
        departments=departments,
        selected_department=department,
        search=search,
        edit_student=None
    )

# ==========================================
# ADD STUDENT
# ==========================================
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"].strip()
    age = request.form["age"]
    department = request.form["department"].strip()
    email = request.form.get("email", "").strip()
    gpa = request.form.get("gpa", "0.00")
    status = request.form.get("status", "Active").strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students
        (name, age, department, email, gpa, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (name, age, department, email, gpa, status)
    )
    conn.commit()
    cur.close()
    conn.close()
    flash("Student added successfully!", "success")
    return redirect("/")

# ==========================================
# DELETE
# ==========================================
@app.route("/delete/<int:id>")
def delete_student(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )
    conn.commit()
    cur.close()
    conn.close()
    flash("Student deleted successfully!", "danger")
    return redirect("/")

# ==========================================
# EDIT (HTML Fallback)
# ==========================================
@app.route("/edit/<int:id>")
def edit_student(id):
    conn = get_connection()
    cur = conn.cursor()
    
    # Selected Student
    cur.execute(
        "SELECT id, name, age, department, email, gpa, status FROM students WHERE id=%s",
        (id,)
    )
    student = cur.fetchone()

    # Dashboard Stats
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT department) FROM students")
    total_departments = cur.fetchone()[0]

    cur.execute("SELECT ROUND(AVG(gpa), 2) FROM students")
    avg_gpa_val = cur.fetchone()[0]
    avg_gpa = float(avg_gpa_val) if avg_gpa_val is not None else 0.00

    cur.execute("SELECT COUNT(*) FROM students WHERE status='Active'")
    active_students = cur.fetchone()[0]

    # Department stats for Chart.js
    cur.execute("""
        SELECT department, COUNT(*), ROUND(AVG(gpa), 2)
        FROM students
        GROUP BY department
        ORDER BY department
    """)
    dept_stats = cur.fetchall()

    # Departments List for Filter
    cur.execute("""
        SELECT DISTINCT department
        FROM students
        ORDER BY department
    """)
    departments = cur.fetchall()

    # Students List
    cur.execute("""
        SELECT id, name, age, department, email, gpa, status
        FROM students
        ORDER BY id
    """)
    students = cur.fetchall()

    cur.close()
    conn.close()
    return render_template(
        "index.html",
        students=students,
        edit_student=student,
        total_students=total_students,
        total_departments=total_departments,
        avg_gpa=avg_gpa,
        active_students=active_students,
        dept_stats=dept_stats,
        departments=departments,
        selected_department="",
        search=""
    )

# ==========================================
# UPDATE
# ==========================================
@app.route("/update/<int:id>", methods=["POST"])
def update_student(id):
    name = request.form["name"].strip()
    age = request.form["age"]
    department = request.form["department"].strip()
    email = request.form.get("email", "").strip()
    gpa = request.form.get("gpa", "0.00")
    status = request.form.get("status", "Active").strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE students
        SET name=%s, age=%s, department=%s, email=%s, gpa=%s, status=%s
        WHERE id=%s
        """,
        (name, age, department, email, gpa, status, id)
    )
    conn.commit()
    cur.close()
    conn.close()
    flash("Student updated successfully!", "info")
    return redirect("/")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)