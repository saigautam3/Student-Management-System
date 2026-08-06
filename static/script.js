// ==================================================
// THEME SWITCHER
// ==================================================
const themeToggleBtn = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

// Load stored theme or default to light
const storedTheme = localStorage.getItem('theme') || 'light';
if (storedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    document.body.classList.remove('light-theme');
    themeIcon.textContent = 'light_mode';
} else {
    document.body.classList.add('light-theme');
    document.body.classList.remove('dark-theme');
    themeIcon.textContent = 'dark_mode';
}

themeToggleBtn.addEventListener('click', () => {
    if (document.body.classList.contains('light-theme')) {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        themeIcon.textContent = 'light_mode';
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        themeIcon.textContent = 'dark_mode';
        localStorage.setItem('theme', 'light');
    }
    // Update charts to match new theme colors
    renderCharts();
});

// ==================================================
// MODAL CONTROLLERS
// ==================================================
const studentModal = document.getElementById('studentModal');
const openAddModalBtn = document.getElementById('openAddModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelFormBtn = document.getElementById('cancelFormBtn');
const studentForm = document.getElementById('studentForm');
const modalTitle = document.getElementById('modalTitle');
const submitFormBtn = document.getElementById('submitFormBtn');

// Modal Elements
const inputName = document.getElementById('studentName');
const inputEmail = document.getElementById('studentEmail');
const inputAge = document.getElementById('studentAge');
const inputGpa = document.getElementById('studentGpa');
const inputDept = document.getElementById('studentDept');
const inputStatus = document.getElementById('studentStatus');

function openAddModal() {
    modalTitle.textContent = "Add New Student";
    submitFormBtn.textContent = "Add Student";
    studentForm.action = "/add";
    
    // Clear fields
    inputName.value = "";
    inputEmail.value = "";
    inputAge.value = "";
    inputGpa.value = "";
    inputDept.value = "";
    inputStatus.value = "Active";

    studentModal.classList.add('active');
}

function openEditModal(student) {
    modalTitle.textContent = "Edit Student Record";
    submitFormBtn.textContent = "Save Changes";
    studentForm.action = `/update/${student.id}`;
    
    // Populate inputs
    inputName.value = student.name;
    inputEmail.value = student.email;
    inputAge.value = student.age;
    inputGpa.value = student.gpa;
    inputDept.value = student.department;
    inputStatus.value = student.status || "Active";

    studentModal.classList.add('active');
}

function closeModal() {
    studentModal.classList.remove('active');
}

// Attach listeners
if (openAddModalBtn) openAddModalBtn.addEventListener('click', openAddModal);
if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
if (cancelFormBtn) cancelFormBtn.addEventListener('click', closeModal);

// Close on outside click
studentModal.addEventListener('click', (e) => {
    if (e.target === studentModal) closeModal();
});

// Expose openEditModal globally for inline button onclick calls
window.openEditModal = openEditModal;

// ==================================================
// SEARCH & FILTERING (Instant Client-side)
// ==================================================
const searchInput = document.getElementById("searchInput");

if (searchInput) {
    searchInput.addEventListener("input", function() {
        const filter = this.value.toLowerCase();
        const rows = document.querySelectorAll("#studentTable tbody tr");
        
        rows.forEach(row => {
            if (row.querySelector(".empty-state")) return;
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(filter) ? "" : "none";
        });
    });
}

function filterDepartment() {
    const department = document.getElementById("departmentFilter").value;
    let url = "/";
    if (department) {
        url += "?department=" + encodeURIComponent(department);
    }
    window.location.href = url;
}
window.filterDepartment = filterDepartment;

// ==================================================
// TABLE DYNAMIC SORTING
// ==================================================
let sortDirections = {};

function sortTable(columnIndex) {
    const table = document.getElementById("studentTable");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));
    
    // Skip if empty state row
    if (rows.length === 1 && rows[0].querySelector(".empty-state")) return;

    const currentDirection = sortDirections[columnIndex] || 'asc';
    const nextDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    sortDirections[columnIndex] = nextDirection;

    // Update icons
    const headers = table.querySelectorAll("th.sortable");
    headers.forEach((th, idx) => {
        const icon = th.querySelector(".sort-icon");
        if (idx === columnIndex) {
            icon.textContent = nextDirection === 'asc' ? 'arrow_upward' : 'arrow_downward';
            icon.style.opacity = "1";
        } else {
            icon.textContent = 'unfold_more';
            icon.style.opacity = "0.6";
        }
    });

    rows.sort((a, b) => {
        let cellA = a.cells[columnIndex].innerText.trim();
        let cellB = b.cells[columnIndex].innerText.trim();

        // Handle numeric sorting (Age, GPA, SL No)
        if (columnIndex === 0 || columnIndex === 3 || columnIndex === 5) {
            const numA = parseFloat(cellA);
            const numB = parseFloat(cellB);
            if (!isNaN(numA) && !isNaN(numB)) {
                return nextDirection === 'asc' ? numA - numB : numB - numA;
            }
        }

        // Default alphabetical sorting
        return nextDirection === 'asc' 
            ? cellA.localeCompare(cellB) 
            : cellB.localeCompare(cellA);
    });

    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}
window.sortTable = sortTable;

// ==================================================
// CSV EXPORTER
// ==================================================
const exportBtn = document.getElementById('exportBtn');
if (exportBtn) {
    exportBtn.addEventListener('click', () => {
        const table = document.getElementById("studentTable");
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        
        // Check if empty
        if (rows.length === 1 && rows[0].querySelector(".empty-state")) {
            alert("No records to export.");
            return;
        }

        let csvContent = "SL No,Name,Email,Age,Department,GPA,Status\n";

        rows.forEach(row => {
            const slNo = row.cells[0].innerText.trim();
            const name = row.cells[1].querySelector(".student-name")?.innerText.trim() || row.cells[1].innerText.trim();
            const email = row.cells[2].innerText.trim();
            const age = row.cells[3].innerText.trim();
            const dept = row.cells[4].innerText.trim();
            const gpa = row.cells[5].innerText.trim();
            const status = row.cells[6].innerText.trim();

            const rowData = [
                slNo,
                `"${name.replace(/"/g, '""')}"`,
                `"${email.replace(/"/g, '""')}"`,
                age,
                `"${dept.replace(/"/g, '""')}"`,
                gpa,
                `"${status.replace(/"/g, '""')}"`
            ];

            csvContent += rowData.join(",") + "\n";
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `student_registry_${new Date().toISOString().slice(0, 10)}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
}

// ==================================================
// CHART.JS DASHBOARD REPORT
// ==================================================
let deptChart = null;
let gpaChart = null;

function renderCharts() {
    const isDark = document.body.classList.contains('dark-theme');
    const labelColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? 'rgba(75, 85, 99, 0.2)' : 'rgba(226, 232, 240, 0.8)';
    const textFamily = "'Outfit', sans-serif";

    // Read chart data bridge
    const dataBridge = document.getElementById('dept-stats-data');
    if (!dataBridge) return;

    const statsData = JSON.parse(dataBridge.textContent || '[]');
    if (statsData.length === 0) return;

    const departments = statsData.map(d => d.department);
    const studentCounts = statsData.map(d => d.count);
    const averageGpas = statsData.map(d => d.avg_gpa);

    if (deptChart) deptChart.destroy();
    if (gpaChart) gpaChart.destroy();

    // Chart 1: Student distribution (Doughnut)
    const ctx1 = document.getElementById('deptDistributionChart');
    if (ctx1) {
        deptChart = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: departments,
                datasets: [{
                    data: studentCounts,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.75)', 
                        'rgba(16, 185, 129, 0.75)', 
                        'rgba(245, 158, 11, 0.75)',  
                        'rgba(14, 165, 233, 0.75)',  
                        'rgba(139, 92, 246, 0.75)',  
                        'rgba(236, 72, 153, 0.75)'   
                    ],
                    borderColor: isDark ? '#0f172a' : '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: labelColor,
                            font: { family: textFamily, size: 12 }
                        }
                    }
                }
            }
        });
    }

    // Chart 2: Average GPA by Department (Bar)
    const ctx2 = document.getElementById('deptGpaChart');
    if (ctx2) {
        gpaChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: departments,
                datasets: [{
                    label: 'Average GPA',
                    data: averageGpas,
                    backgroundColor: 'rgba(59, 130, 246, 0.85)',
                    hoverBackgroundColor: 'rgba(37, 99, 235, 1)',
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: labelColor,
                            font: { family: textFamily }
                        }
                    },
                    y: {
                        min: 0,
                        max: 4,
                        grid: { color: gridColor },
                        ticks: {
                            color: labelColor,
                            font: { family: textFamily },
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
}

// Auto-dismiss Flash Notification Toast
setTimeout(() => {
    const toasts = document.querySelectorAll(".toast");
    toasts.forEach(toast => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    });
}, 4000);

// Initialize charts on DOM content loaded
window.addEventListener('DOMContentLoaded', () => {
    renderCharts();
});
