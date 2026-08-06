# 🎓 StudentSphere - Student Management & Analytics Portal

StudentSphere is a modern, responsive web application for managing academic records and exploring student analytics. Built with **Flask** and **PostgreSQL**, it demonstrates a complete database-driven CRUD (Create, Read, Update, Delete) workflow with a clean glassmorphic UI, real-time client-side interactivity, and dynamic charts.

---

## 🚀 Key Features (A to Z)

- **A - Academic Statistics Dashboard**: Displays key high-level statistics at a glance:
  - *Total Students* enrolled in the system.
  - *Active Enrolled* count.
  - *Average GPA* of all students (automatically calculated).
  - *Departments count* (number of unique departments).
- **B - Bar & Doughnut Analytics Charts**: Integrated **Chart.js** dashboard featuring:
  - A *Doughnut Chart* displaying the student distribution by department.
  - A *Bar Chart* showing the average GPA per department.
  - Interactive hover highlights and legends.
- **C - Client-Side Search**: A real-time, case-insensitive search bar that filters the student registry instantly as you type.
- **D - Dynamic Theme Switcher**: Full support for both **Light Mode** and **Dark Mode** with smooth transitions. The user's theme preference is persisted in `localStorage` and charts automatically redraw to match the selected theme's color palette.
- **E - Export to CSV**: A single-click utility that compiles the current student registry into a standard `.csv` spreadsheet file and triggers a browser download.
- **F - Flash Notifications (Toasts)**: System events (adding, updating, or deleting students) trigger modern, self-dismissing toast notifications colored by category (success, info, danger).
- **G - GPA Scale (0.00 to 10.00)**: Supports standard 10-point grading scales. GPAs are highlighted with color-coded badges based on performance:
  - `gpa-excellent` (Green badge): $\ge$ 8.50
  - `gpa-good` (Blue badge): 7.50 to 8.49
  - `gpa-average` (Orange badge): $<$ 7.50
- **H - HTML5 Form Validation**: The Add/Edit student form utilizes strict HTML5 validations for data types (email, numbers), minimum/maximum bounds (ages, GPAs), and required fields.
- **I - Interactive Modals**: Add and Edit operations are housed in clean, overlay-based modal forms that slide into view to preserve space and user context.
- **L - Live Database Syncing**: Fully backed by PostgreSQL to ensure immediate data updates and ACID transaction compliance.
- **P - Profile Avatars**: Renders circular profile avatars dynamically utilizing the first letter of the student's name.
- **R - Responsive Grid Layout**: Built using a modern CSS Grid/Flexbox design system that adjusts seamlessly to mobile, tablet, and desktop screens.
- **S - Smart Table Sorting**: Toggleable sorting (ascending and descending) for table columns including *SL No*, *Name*, *Email*, *Age*, *Department*, and *GPA* with responsive sort indicator icons.

---

## 🛠️ Tech Stack

- **Frontend:**
  - **HTML5 & CSS3:** Responsive layouts using CSS variables, glassmorphism design, and animations.
  - **JavaScript (Vanilla ES6):** Client-side searching, sorting, CSV export, theme toggling, and modal controls.
  - **Chart.js:** Dynamic data rendering for analytics.
  - **Google Fonts & Material Icons:** Typography ('Outfit') and iconography.
- **Backend:**
  - **Flask (Python):** Route handlers, session/flash notifications, templates (Jinja2).
  - **psycopg2-binary:** PostgreSQL database adapter.
  - **Gunicorn:** Production WSGI HTTP server configuration.
- **Database:**
  - **PostgreSQL:** Relational database management.

---

## 📂 Project Structure

```text
Student-Management/
├── app.py              # Main Flask application with routes & controllers
├── database.py         # PostgreSQL database connection configuration
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
│
├── static/
│   ├── style.css       # Clean, modern custom design system & light/dark theme rules
│   └── script.js       # Theme switching, modal management, charts, and CSV utilities
│
└── templates/
    └── index.html      # Jinja2 template for the portal dashboard and modals
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

### 2. Set Up a Virtual Environment (Optional but Recommended)
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
2. Connect to `studentdb` and run the database schema definition:
   ```sql
   CREATE TABLE students (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       age INT NOT NULL,
       department VARCHAR(100) NOT NULL,
       email VARCHAR(150),
       gpa NUMERIC(4, 2) CHECK (gpa >= 0.00 AND gpa <= 10.00),
       status VARCHAR(20) DEFAULT 'Active'
   );
   ```

### 5. Configure Credentials
Update your database configuration inside `database.py` with your username, password, host, and port:
```python
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="studentdb",
        user="your_username",
        password="your_password",
        port="5432"
    )
```

### 6. Run the Application
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## 👨‍💻 Author

**Sai Gautam**
- GitHub: [@saigautam3](https://github.com/saigautam3)