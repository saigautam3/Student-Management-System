from flask import Flask, render_template, request, redirect, flash
from database import get_connection
app = Flask(__name__)
app.secret_key = "student_management_secret"

# ==========================================
# HOME
# ==========================================
@app.route("/")
def home():

    search = request.args.get("search", "")
    department = request.args.get("department", "")
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- Dashboard ----------------
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(DISTINCT department)
        FROM students
    """)
    total_departments = cur.fetchone()[0]

    # ---------------- Departments ----------------
    cur.execute("""
        SELECT DISTINCT department
        FROM students
        ORDER BY department
    """)
    departments = cur.fetchall()

    # ---------------- Students ----------------
    query = """
        SELECT *
        FROM students
        WHERE
        name ILIKE %s
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
        departments=departments,
        selected_department=department,
        search=search
    )

# ==========================================
# ADD STUDENT
# ==========================================
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"].strip()
    age = request.form["age"]
    department = request.form["department"].strip()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students
        (name, age, department)
        VALUES(%s,%s,%s)
        """,
        (name, age, department)
    )
    conn.commit()
    flash("Student added successfully!", "success")
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
    flash("Student deleted successfully!", "danger")
    cur.close()
    conn.close()
    flash("Student deleted successfully!", "danger")
    return redirect("/")

# ==========================================
# EDIT
# ==========================================
@app.route("/edit/<int:id>")
def edit_student(id):
    conn = get_connection()
    cur = conn.cursor()
    # Student
    cur.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )
    student = cur.fetchone()

    # Dashboard
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(DISTINCT department)
        FROM students
    """)
    total_departments = cur.fetchone()[0]

    # Departments
    cur.execute("""
        SELECT DISTINCT department
        FROM students
        ORDER BY department
    """)
    departments = cur.fetchall()

    # Students
    cur.execute("""
        SELECT *
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE students
        SET
        name=%s,
        age=%s,
        department=%s
        WHERE id=%s
    """,
    (name, age, department, id)
    )
    conn.commit()
    flash("Student updated successfully!", "info")
    cur.close()
    conn.close()
    flash("Student updated successfully!", "info")
    return redirect("/")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)