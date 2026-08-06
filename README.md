# 🎓 StudentSphere - Faculty Management & Analytics Portal

StudentSphere is a modern, production-quality academic ERP and analytics portal designed for faculty members to manage student records, monitor departmental statistics, and log actions. Built with **Flask** and **PostgreSQL**, it demonstrates a complete database-driven CRUD workflow with a secure authentication system, real-time client-side interactivity, and dynamic charts.

---

## 🚀 Key Features (A to Z)

- **A - Academic Statistics Dashboard**: Displays key high-level statistics at a glance:
  - *Total Students* enrolled in the system.
  - *Active / Inactive / Graduated* student ratios.
  - *Average GPA* of all students (automatically calculated).
  - *Top Performer* and *Lowest GPA* metrics.
  - *Recently Added Student* tracker.
- **B - Bar, Doughnut & Line Analytics Charts**: Integrated **Chart.js** dashboard featuring:
  - *Department Distribution* (Doughnut Chart)
  - *Average GPA by Department* (Bar Chart)
  - *GPA Range Distribution* (Bar Chart)
  - *Status Distribution* (Pie Chart)
  - *Age Distribution* (Bar Chart)
  - *Admissions Growth Trend* (Line/Area Chart representing cumulative growth over time)
- **C - Client-Side Search & Sorting**: Real-time, responsive column sorting (SL No, Name, Email, Age, Department, GPA, and Status) and text search.
- **D - Dynamic Theme Switcher**: Full support for both **Light Mode** and **Dark Mode** with smooth transitions. The theme preference is saved in `localStorage` and charts automatically adapt their color theme.
- **E - Export Options**: Export student records instantly to multiple formats:
  - Download current registry as a **CSV** file.
  - Export filtered rows directly to **Excel (`.xlsx`)** spreadsheets using SheetJS.
  - Compile the registry table into a **PDF** report document using `html2pdf.js`.
  - Print report layout stylesheets.
- **F - Flash Notifications (Toasts)**: System operations trigger modern, self-dismissing toast notifications colored by type (success, info, danger, warning).
- **G - GPA Scale (0.00 to 10.00)**: Supports standard 10-point grading scales. GPAs are highlighted with color-coded badges based on performance:
  - `gpa-excellent` (Green badge): $\ge$ 8.50
  - `gpa-good` (Blue badge): 7.50 to 8.49
  - `gpa-average` (Orange badge): $<$ 7.50
- **H - HTML5 & Backend Data Validation**: Validates all fields against duplicate email records, secure username parameters, and password complexity requirements.
- **I - Interactive Modals**: Slid-in overlay modal forms for adding/editing students and departments, and a custom confirmation modal replacing standard browser `confirm()` prompts.
- **L - Live Database Syncing**: Fully backed by PostgreSQL to ensure immediate data updates and ACID transaction compliance.
- **M - Multi-Criteria Filter Grid**: Dynamic filter toolbar allowing users to query records by Name, Department, Enrollment Status, Age, and GPA range simultaneously.
- **P - Profile Pages & Picture Upload**: Renders circular profile avatars or uploaded profile photos on individual student profile screens showing academic records and historical logs.
- **R - Responsive Grid Layout**: Built using a modern CSS Grid/Flexbox design system that adjusts seamlessly to mobile, tablet, and desktop screens.
- **S - Secure Authentication Settings**: Features password validation filters (at least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char) and options to update Faculty Profile usernames and emails directly from the portal.

---

## 🛠️ Tech Stack

- **Frontend:**
  - **HTML5 & CSS3:** Custom design system using variables, glassmorphism design, and transitions.
  - **JavaScript (Vanilla ES6):** Client-side pagination, sorting, CSV/Excel/PDF exporters, theme toggling, and modal controls.
  - **Chart.js:** Multi-graph analytics visualization.
  - **CDN Dependencies:** SheetJS (`xlsx.full.min.js`), html2pdf.js, Google Fonts (Outfit), Google Material Icons.
- **Backend:**
  - **Flask (Python):** Route handlers, session management, secure uploads, and templates (Jinja2).
  - **psycopg2-binary:** PostgreSQL database adapter.
  - **Werkzeug Security:** Password hashing (`generate_password_hash`, `check_password_hash`).
- **Database:**
  - **PostgreSQL:** Relational database management.

---

## 📂 Project Structure

```text
Student-Management/
├── app.py                  # Flask application routes, session validation & file handling
├── database.py             # PostgreSQL connection and activity logging helpers
├── migrate_dashboard.py    # Database schema migration & initialization script
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── static/
│   ├── style.css           # Modern sidebar dashboard styling & theme configurations
│   ├── script.js           # Multi-charts, pagination, sorting, checkboxes, and exporters
│   └── uploads/            # (Auto-created) Stores uploaded profile pictures
│
└── templates/
    ├── index.html          # Main portal dashboard, filters, modals, and tables
    ├── login.html          # Secure faculty portal login screen
    ├── profile.html        # Detailed student information & timeline records
    ├── departments.html    # Academic department list, statistics, and CRUD forms
    └── settings.html       # Change password & update profile settings panel
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL server (running locally or in the cloud)

### 1. Clone the Repository
```bash
git clone https://github.com/saigautam3/Student-Management-System.git
cd Student-Management-System
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
1. Log into your PostgreSQL instance and create a database named `studentdb`:
   ```sql
   CREATE DATABASE studentdb;
   ```
2. Connect to `studentdb` and run the database schema definitions:
   ```sql
   -- 1. Departments table
   CREATE TABLE departments (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) UNIQUE NOT NULL,
       code VARCHAR(20) UNIQUE NOT NULL,
       description TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- 2. Students registry table
   CREATE TABLE students (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       age INT NOT NULL,
       department_id INT REFERENCES departments(id) ON DELETE SET NULL,
       email VARCHAR(150) UNIQUE,
       gpa NUMERIC(4, 2) CHECK (gpa >= 0.00 AND gpa <= 10.00),
       status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Graduated')),
       image_path VARCHAR(255),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- 3. Users authentication table
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       username VARCHAR(50) UNIQUE NOT NULL,
       password_hash VARCHAR(255) NOT NULL,
       email VARCHAR(100),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- 4. Activity Logs table
   CREATE TABLE activity_logs (
       id SERIAL PRIMARY KEY,
       action VARCHAR(100) NOT NULL,
       details TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 5. Run DB Migrations & Initialize Default User
To automatically create the tables, migrate existing data, and insert the default Faculty login:
```bash
python migrate_dashboard.py
```

### 6. Configure Credentials
Update your database configuration inside `database.py` with your username, password, host, and port:
```python
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="studentdb",
        user="your_username",
        password="your_password",
        port="5432"
    )
```

### 7. Run the Application
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## 🔑 Default Credentials

Log in using these default credentials (you can change them in the Settings page after logging in):
- **Username:** `faculty`
- **Password:** `FacultyPass123!`

---

## 👨‍💻 Author

**Sai Gautam**
- GitHub: [@saigautam3](https://github.com/saigautam3)