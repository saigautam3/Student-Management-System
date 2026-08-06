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
    if (themeIcon) themeIcon.textContent = 'light_mode';
} else {
    document.body.classList.add('light-theme');
    document.body.classList.remove('dark-theme');
    if (themeIcon) themeIcon.textContent = 'dark_mode';
}

if (themeToggleBtn) {
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
}

// ==================================================
// TABS / SECTIONS SWITCHER
// ==================================================
function switchTab(targetId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar-menu .menu-item').forEach(el => el.classList.remove('active'));
    
    const targetEl = document.querySelector(targetId);
    if (targetEl) {
        targetEl.classList.add('active');
        
        // Update sidebar active menu item and title label
        if (targetId === '#dashboard-section') {
            document.getElementById('menu-dashboard').classList.add('active');
            document.getElementById('page-title-label').textContent = "Dashboard Overview";
        } else if (targetId === '#registry-section') {
            document.getElementById('menu-registry').classList.add('active');
            document.getElementById('page-title-label').textContent = "Student Registry";
        }
    }
}

// Sidebar click triggers
document.querySelectorAll('.sidebar-menu .menu-item').forEach(item => {
    item.addEventListener('click', (e) => {
        const href = item.getAttribute('href');
        if (href.startsWith('#')) {
            e.preventDefault();
            switchTab(href);
            window.location.hash = href;
        }
    });
});

// Sync hash on initial load
window.addEventListener('DOMContentLoaded', () => {
    // If query filters are active, default to registry
    const urlParams = new URLSearchParams(window.location.search);
    const hasFilters = urlParams.has('search') || urlParams.has('department') || urlParams.has('status') || urlParams.has('gpa_min') || urlParams.has('gpa_max') || urlParams.has('age');
    
    if (hasFilters || window.location.hash === '#registry-section') {
        switchTab('#registry-section');
    } else {
        switchTab('#dashboard-section');
    }
    
    
    renderCharts();
    initPagination();
    initBulkSelection();

    // Notification center toggle
    const bellBtn = document.getElementById("notifBellBtn");
    const dropdown = document.getElementById("notifDropdown");
    if (bellBtn && dropdown) {
        bellBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === "none" ? "flex" : "none";
        });
        document.addEventListener("click", () => {
            dropdown.style.display = "none";
        });
        dropdown.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }

    // Advanced search engine listener
    const searchInput = document.getElementById("regSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", runEnterpriseSearch);
    }
});

// ==================================================
// STUDENT MODAL CONTROLLERS (ADD/EDIT)
// ==================================================
const studentModal = document.getElementById('studentModal');
const openAddModalBtn = document.getElementById('openAddModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelFormBtn = document.getElementById('cancelFormBtn');
const studentForm = document.getElementById('studentForm');
const modalTitle = document.getElementById('modalTitle');
const submitFormBtn = document.getElementById('submitFormBtn');

// Modal Input Fields
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
    
    // Populate fields
    inputName.value = student.name;
    inputEmail.value = student.email;
    inputAge.value = student.age;
    inputGpa.value = student.gpa;
    inputDept.value = student.department_id;
    inputStatus.value = student.status || "Active";

    studentModal.classList.add('active');
}

function closeModal() {
    studentModal.classList.remove('active');
}

// Attach modal events
if (openAddModalBtn) openAddModalBtn.addEventListener('click', openAddModal);
if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
if (cancelFormBtn) cancelFormBtn.addEventListener('click', closeModal);

if (studentModal) {
    studentModal.addEventListener('click', (e) => {
        if (e.target === studentModal) closeModal();
    });
}

window.openEditModal = openEditModal;

// ==================================================
// DELETE CONFIRMATION MODAL
// ==================================================
const confirmDeleteModal = document.getElementById("confirmDeleteModal");
const deleteStudentLabel = document.getElementById("deleteStudentLabel");
const confirmDeleteLink = document.getElementById("confirmDeleteLink");

function triggerConfirmDelete(id, name) {
    if (deleteStudentLabel && confirmDeleteLink && confirmDeleteModal) {
        deleteStudentLabel.textContent = name;
        confirmDeleteLink.href = `/delete/${id}`;
        confirmDeleteModal.classList.add("active");
    }
}

function closeConfirmDeleteModal() {
    if (confirmDeleteModal) {
        confirmDeleteModal.classList.remove("active");
    }
}

if (confirmDeleteModal) {
    confirmDeleteModal.addEventListener("click", (e) => {
        if (e.target === confirmDeleteModal) closeConfirmDeleteModal();
    });
}

window.triggerConfirmDelete = triggerConfirmDelete;
window.closeConfirmDeleteModal = closeConfirmDeleteModal;

// ==================================================
// TABLE PAGINATION SYSTEM
// ==================================================
let currentPage = 1;
const rowsPerPage = 10;
let tableRows = [];

function initPagination() {
    const tableBody = document.getElementById("studentTableBody");
    if (!tableBody) return;
    
    tableRows = Array.from(tableBody.querySelectorAll("tr"));
    
    // Check if empty state is showing
    if (tableRows.length === 1 && tableRows[0].querySelector(".empty-state")) {
        const pag = document.getElementById("tablePagination");
        if (pag) pag.style.display = "none";
        return;
    }

    paginate(currentPage);
}

function paginate(page) {
    const totalPages = Math.ceil(tableRows.length / rowsPerPage);
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    
    currentPage = page;

    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    tableRows.forEach((row, index) => {
        if (index >= start && index < end) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });

    const infoLabel = document.getElementById("paginationInfoLabel");
    if (infoLabel) {
        infoLabel.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    }

    const prevBtn = document.getElementById("paginationPrevBtn");
    const nextBtn = document.getElementById("paginationNextBtn");
    
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalPages === 0;
}

function nextPage() {
    paginate(currentPage + 1);
}

function prevPage() {
    paginate(currentPage - 1);
}

window.nextPage = nextPage;
window.prevPage = prevPage;

// ==================================================
// TABLE DYNAMIC SORTING
// ==================================================
let sortDirections = {};

function sortTable(columnIndex) {
    const table = document.getElementById("studentTable");
    const tbody = table.querySelector("tbody");
    // Sort all rows, ignoring pagination hidden states
    const rows = Array.from(tbody.querySelectorAll("tr"));
    
    if (rows.length === 1 && rows[0].querySelector(".empty-state")) return;

    const currentDirection = sortDirections[columnIndex] || 'asc';
    const nextDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    sortDirections[columnIndex] = nextDirection;

    // Reset indicator icons
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

    // Checkbox is at index 0, so SL is cell[1], Name is cell[2], etc.
    const actualCellIndex = columnIndex + 1;

    rows.sort((a, b) => {
        let cellA = a.cells[actualCellIndex].innerText.trim();
        let cellB = b.cells[actualCellIndex].innerText.trim();

        // Numeric fields: SL No (1), Age (4), GPA (6)
        if (actualCellIndex === 1 || actualCellIndex === 4 || actualCellIndex === 6) {
            const numA = parseFloat(cellA);
            const numB = parseFloat(cellB);
            if (!isNaN(numA) && !isNaN(numB)) {
                return nextDirection === 'asc' ? numA - numB : numB - numA;
            }
        }

        // Alphabetical sorting
        return nextDirection === 'asc' 
            ? cellA.localeCompare(cellB) 
            : cellB.localeCompare(cellA);
    });

    // Re-append sorted rows and reset pagination view
    rows.forEach(row => tbody.appendChild(row));
    initPagination();
}
window.sortTable = sortTable;

// ==================================================
// BULK OPERATIONS
// ==================================================
function initBulkSelection() {
    const selectAll = document.getElementById("selectAllCheckbox");
    const rowCheckboxes = document.querySelectorAll(".row-checkbox");
    const bulkToolbar = document.getElementById("bulkToolbar");
    const selectedCountLabel = document.getElementById("bulkSelectedCount");

    if (!selectAll) return;

    selectAll.addEventListener("change", function() {
        rowCheckboxes.forEach(cb => {
            cb.checked = selectAll.checked;
            const tr = cb.closest("tr");
            if (selectAll.checked) {
                tr.classList.add("row-selected");
            } else {
                tr.classList.remove("row-selected");
            }
        });
        updateBulkToolbarState();
    });

    rowCheckboxes.forEach(cb => {
        cb.addEventListener("change", function() {
            const tr = cb.closest("tr");
            if (cb.checked) {
                tr.classList.add("row-selected");
            } else {
                tr.classList.remove("row-selected");
            }
            // Sync selectAll
            const allChecked = Array.from(rowCheckboxes).every(c => c.checked);
            selectAll.checked = allChecked;
            updateBulkToolbarState();
        });
    });

    function updateBulkToolbarState() {
        const checkedCount = document.querySelectorAll(".row-checkbox:checked").length;
        if (checkedCount > 0) {
            bulkToolbar.classList.add("active");
            selectedCountLabel.textContent = checkedCount;
        } else {
            bulkToolbar.classList.remove("active");
        }
    }
}

function submitBulkAction(action) {
    const bulkActionInput = document.getElementById("bulkActionInput");
    const bulkForm = document.getElementById("bulkForm");
    const selectedCount = document.querySelectorAll(".row-checkbox:checked").length;

    if (action === 'delete') {
        if (!confirm(`Are you sure you want to delete the ${selectedCount} selected students?`)) {
            return;
        }
    }

    if (bulkActionInput && bulkForm) {
        bulkActionInput.value = action;
        bulkForm.submit();
    }
}

window.submitBulkAction = submitBulkAction;

// ==================================================
// DOCUMENT EXPORTERS
// ==================================================

// 1. CSV EXPORT (Visible rows)
function exportTableToCSV() {
    const table = document.getElementById("studentTable");
    const rows = Array.from(table.querySelectorAll("tbody tr"));
    
    if (rows.length === 1 && rows[0].querySelector(".empty-state")) {
        alert("No records to export.");
        return;
    }

    let csvContent = "SL No,Name,Email,Age,Department,GPA,Status\n";

    rows.forEach(row => {
        if (row.style.display === "none") return; // Export only current visible page / filtered rows

        const slNo = row.cells[1].innerText.trim();
        const name = row.cells[2].querySelector(".student-name")?.innerText.trim() || row.cells[2].innerText.trim();
        const email = row.cells[3].innerText.trim();
        const age = row.cells[4].innerText.trim();
        const dept = row.cells[5].innerText.trim();
        const gpa = row.cells[6].innerText.trim();
        const status = row.cells[7].innerText.trim();

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
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 2. EXCEL EXPORT (using SheetJS from CDN)
function exportTableToExcel() {
    const table = document.getElementById("studentTable");
    const rows = Array.from(table.querySelectorAll("tbody tr"));
    
    if (rows.length === 1 && rows[0].querySelector(".empty-state")) {
        alert("No records to export.");
        return;
    }

    let data = [];
    rows.forEach((row) => {
        if (row.style.display === "none") return; // Filtered rows only
        
        const slNo = row.cells[1].innerText.trim();
        const name = row.cells[2].querySelector(".student-name")?.innerText.trim() || row.cells[2].innerText.trim();
        const email = row.cells[3].innerText.trim();
        const age = row.cells[4].innerText.trim();
        const dept = row.cells[5].innerText.trim();
        const gpa = row.cells[6].innerText.trim();
        const status = row.cells[7].innerText.trim();
        
        data.push({
            "SL No": parseInt(slNo),
            "Name": name,
            "Email": email,
            "Age": parseInt(age),
            "Department": dept,
            "GPA": parseFloat(gpa),
            "Status": status
        });
    });

    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Student Registry");
    XLSX.writeFile(workbook, `student_registry_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

// 3. PDF EXPORT (using html2pdf.js from CDN)
function exportTableToPDF() {
    const element = document.querySelector(".table-container");
    if (!element) return;
    
    const opt = {
        margin:       0.5,
        filename:     `student_registry_${new Date().toISOString().slice(0,10)}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'landscape' }
    };
    html2pdf().set(opt).from(element).save();
}

// 4. PRINT REPORT
function printReport() {
    window.print();
}

// 5. BULK CSV EXPORT
function bulkExportCSV() {
    const selectedCheckboxes = document.querySelectorAll(".row-checkbox:checked");
    if (selectedCheckboxes.length === 0) return;
    
    let csvContent = "SL No,Name,Email,Age,Department,GPA,Status\n";
    selectedCheckboxes.forEach((cb, index) => {
        const row = cb.closest("tr");
        const slNo = index + 1;
        const name = row.cells[2].querySelector(".student-name")?.innerText.trim() || row.cells[2].innerText.trim();
        const email = row.cells[3].innerText.trim();
        const age = row.cells[4].innerText.trim();
        const dept = row.cells[5].innerText.trim();
        const gpa = row.cells[6].innerText.trim();
        const status = row.cells[7].innerText.trim();
        
        csvContent += `${slNo},"${name.replace(/"/g, '""')}","${email.replace(/"/g, '""')}",${age},"${dept.replace(/"/g, '""')}",${gpa},"${status.replace(/"/g, '""')}"\n`;
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `bulk_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Clear Filters Helper
function clearAllFilters(e) {
    e.preventDefault();
    window.location.href = "/#registry-section";
}

window.exportTableToCSV = exportTableToCSV;
window.exportTableToExcel = exportTableToExcel;
window.exportTableToPDF = exportTableToPDF;
window.printReport = printReport;
window.bulkExportCSV = bulkExportCSV;
window.clearAllFilters = clearAllFilters;

// ==================================================
// CHART.JS DASHBOARD REPORT (6 CHARTS)
// ==================================================
let chartsInstance = {};

function renderCharts() {
    const isDark = document.body.classList.contains('dark-theme');
    const labelColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? 'rgba(75, 85, 99, 0.2)' : 'rgba(226, 232, 240, 0.8)';
    const textFamily = "'Outfit', sans-serif";

    // Read chart data bridge
    const dataBridge = document.getElementById('analytics-data-bridge');
    if (!dataBridge) return;

    const data = JSON.parse(dataBridge.textContent || '{}');
    if (!data.departments || data.departments.length === 0) return;

    // Color theme helper
    const primaryBg = 'rgba(59, 130, 246, 0.75)';
    const primaryHover = 'rgba(37, 99, 235, 1)';
    const chartColors = [
        'rgba(59, 130, 246, 0.75)', 
        'rgba(16, 185, 129, 0.75)', 
        'rgba(245, 158, 11, 0.75)',  
        'rgba(14, 165, 233, 0.75)',  
        'rgba(139, 92, 246, 0.75)',  
        'rgba(236, 72, 153, 0.75)'   
    ];
    const chartBorderColor = isDark ? '#0f172a' : '#ffffff';

    // Helper to destroy active chart instance
    const cleanChart = (name) => {
        if (chartsInstance[name]) {
            chartsInstance[name].destroy();
        }
    };

    // 1. Department Distribution (Doughnut Chart)
    const ctx1 = document.getElementById('deptDistributionChart');
    if (ctx1) {
        cleanChart('deptDist');
        chartsInstance['deptDist'] = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: data.departments,
                datasets: [{
                    data: data.studentCounts,
                    backgroundColor: chartColors,
                    borderColor: chartBorderColor,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: labelColor, font: { family: textFamily, size: 12 } }
                    }
                }
            }
        });
    }

    // 2. Average GPA by Department (Bar Chart)
    const ctx2 = document.getElementById('deptGpaChart');
    if (ctx2) {
        cleanChart('deptGpa');
        chartsInstance['deptGpa'] = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: data.departments,
                datasets: [{
                    label: 'Average GPA',
                    data: data.avgGpas,
                    backgroundColor: primaryBg,
                    hoverBackgroundColor: primaryHover,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: labelColor, font: { family: textFamily } } },
                    y: { min: 0, max: 10, grid: { color: gridColor }, ticks: { color: labelColor, font: { family: textFamily }, stepSize: 2 } }
                }
            }
        });
    }

    // 3. GPA Range Distribution (Bar Chart)
    const ctx3 = document.getElementById('gpaDistributionChart');
    if (ctx3) {
        cleanChart('gpaDist');
        chartsInstance['gpaDist'] = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: ['< 5.00', '5.00 - 7.49', '7.50 - 8.49', '8.50+'],
                datasets: [{
                    label: 'Students Count',
                    data: data.gpaDist,
                    backgroundColor: 'rgba(139, 92, 246, 0.75)',
                    hoverBackgroundColor: 'rgba(124, 58, 237, 1)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: labelColor, font: { family: textFamily } } },
                    y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: textFamily }, stepSize: 1 } }
                }
            }
        });
    }

    // 4. Status Distribution (Pie Chart)
    const ctx4 = document.getElementById('statusDistributionChart');
    if (ctx4) {
        cleanChart('statusDist');
        chartsInstance['statusDist'] = new Chart(ctx4, {
            type: 'pie',
            data: {
                labels: ['Active', 'Inactive', 'Graduated'],
                datasets: [{
                    data: [data.statusDist.Active, data.statusDist.Inactive, data.statusDist.Graduated],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.75)', // Active green
                        'rgba(239, 68, 68, 0.75)',  // Inactive red
                        'rgba(59, 130, 246, 0.75)'   // Graduated blue
                    ],
                    borderColor: chartBorderColor,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: labelColor, font: { family: textFamily, size: 12 } }
                    }
                }
            }
        });
    }

    // 5. Age Distribution (Bar Chart)
    const ctx5 = document.getElementById('ageDistributionChart');
    if (ctx5) {
        cleanChart('ageDist');
        chartsInstance['ageDist'] = new Chart(ctx5, {
            type: 'bar',
            data: {
                labels: ['Under 18', '18 - 21', '22 - 25', '26+'],
                datasets: [{
                    label: 'Students Count',
                    data: data.ageDist,
                    backgroundColor: 'rgba(245, 158, 11, 0.75)',
                    hoverBackgroundColor: 'rgba(217, 119, 6, 1)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: labelColor, font: { family: textFamily } } },
                    y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: textFamily }, stepSize: 1 } }
                }
            }
        });
    }

    // 6. Admissions Growth Trend (Line Chart)
    const ctx6 = document.getElementById('growthTrendChart');
    if (ctx6) {
        cleanChart('growthTrend');
        chartsInstance['growthTrend'] = new Chart(ctx6, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [
                    {
                        label: 'Monthly Admissions',
                        data: data.monthlyCounts,
                        borderColor: 'rgba(16, 185, 129, 0.8)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Cumulative Students',
                        data: data.cumulativeCounts,
                        borderColor: 'rgba(59, 130, 246, 0.8)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: labelColor, font: { family: textFamily } }
                    }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: labelColor, font: { family: textFamily } } },
                    y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: textFamily }, stepSize: 2 } }
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

// ==================================================
// ENTERPRISE ADVANCED SEARCH ENGINE
// ==================================================
function runEnterpriseSearch() {
    const query = document.getElementById("regSearchInput").value.trim().toLowerCase();
    const rows = document.querySelectorAll("#studentTableBody tr");
    
    if (!query) {
        // Reset rows visibility based on pagination
        updateTableDisplay();
        document.getElementById("tablePagination").style.display = "flex";
        return;
    }

    // Parse search operators
    let filterFn = null;
    const gpaMatch = query.match(/gpa\s*(>|<|=)\s*([0-9.]+)/);
    const ageMatch = query.match(/age\s*(>|<|=)\s*([0-9]+)/);
    const statusMatch = query.match(/status\s*=\s*(\w+)/);
    const deptMatch = query.match(/dept\s*=\s*(\w+)/);

    if (gpaMatch) {
        const op = gpaMatch[1];
        const val = parseFloat(gpaMatch[2]);
        filterFn = (gpa) => {
            if (op === '>') return gpa > val;
            if (op === '<') return gpa < val;
            return gpa === val;
        };
    } else if (ageMatch) {
        const op = ageMatch[1];
        const val = parseInt(ageMatch[2]);
        filterFn = (age) => {
            if (op === '>') return age > val;
            if (op === '<') return age < val;
            return age === val;
        };
    } else if (statusMatch) {
        const val = statusMatch[1];
        filterFn = (status) => status.toLowerCase() === val;
    } else if (deptMatch) {
        const val = deptMatch[1];
        filterFn = (dept) => dept.toLowerCase().includes(val);
    }

    let visibleCount = 0;
    rows.forEach(row => {
        if (row.querySelector("td[colspan]")) return; // skip empty state row
        
        const name = row.querySelector(".student-name").textContent.toLowerCase();
        const email = row.querySelector(".email-link").textContent.toLowerCase();
        const age = parseInt(row.cells[4].textContent);
        const dept = row.cells[5].textContent.trim().toLowerCase();
        const gpa = parseFloat(row.cells[6].textContent);
        const status = row.cells[7].textContent.trim().toLowerCase();

        let match = false;
        if (filterFn) {
            if (gpaMatch) match = filterFn(gpa);
            else if (ageMatch) match = filterFn(age);
            else if (statusMatch) match = filterFn(status);
            else if (deptMatch) match = filterFn(dept);
        } else {
            // General string matching
            match = name.includes(query) || email.includes(query) || dept.includes(query) || status.includes(query);
        }

        if (match) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    // Hide pagination controls during active search
    document.getElementById("tablePagination").style.display = "none";
    document.getElementById("registryCountLabel").textContent = `${visibleCount} records found (filtered)`;
}

// ==================================================
// NOTIFICATIONS & AUDIT EVENT FUNCTIONS
// ==================================================
function markNotifRead(id) {
    fetch(`/notifications/read/${id}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const el = document.getElementById(`notif-item-${id}`);
            if (el) {
                el.classList.remove('notif-unread');
                const markBtn = el.querySelector('button');
                if (markBtn) markBtn.remove();
            }
            // Decrement badge count
            const badge = document.getElementById('notifBadgeCount');
            if (badge) {
                let count = parseInt(badge.textContent) - 1;
                if (count <= 0) badge.remove();
                else badge.textContent = count;
            }
        }
    });
}

function clearAllNotifs() {
    fetch(`/notifications/clear-all`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('notifList').innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted); font-size:12px;">No notifications.</div>';
            const badge = document.getElementById('notifBadgeCount');
            if (badge) badge.remove();
        }
    });
}

function filterTimelineLogs() {
    const val = document.getElementById("timelineFilterSelect").value;
    window.location.href = `/?timeline_filter=${val}#dashboard-section`;
}

// Bind to globals
window.markNotifRead = markNotifRead;
window.clearAllNotifs = clearAllNotifs;
window.filterTimelineLogs = filterTimelineLogs;
