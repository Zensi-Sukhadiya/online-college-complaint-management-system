console.log("College Complaint Management System Loaded");

/* ===========================
   STUDENT LIVE SEARCH
=========================== */

const searchInput = document.getElementById("searchStudent");
const studentTable = document.getElementById("studentTable");

if (searchInput && studentTable) {

    searchInput.addEventListener("keyup", function () {

        let query = this.value;

        fetch(`/admin/students/search?q=${query}`)

            .then(response => response.json())

            .then(data => {

                studentTable.innerHTML = "";

                if (data.length === 0) {

                    studentTable.innerHTML = `
                        <tr>
                            <td colspan="6" class="text-center py-5">
                                No students found
                            </td>
                        </tr>
                    `;

                    return;
                }

                data.forEach(student => {

                    studentTable.innerHTML += `
                        <tr>

                            <td>#${student.id}</td>

                            <td>
                                <i class="bi bi-person-circle me-2"></i>
                                ${student.name}
                            </td>

                            <td>${student.email}</td>

                            <td>${student.department}</td>

                            <td>
                                <span class="badge bg-primary">
                                    ${student.complaints} Registered
                                </span>
                            </td>

                            <td class="text-end">

                                <a href="/admin/student/${student.id}"
                                   class="btn btn-sm btn-outline-primary px-3 me-1">

                                    <i class="bi bi-eye"></i> View

                                </a>

                                <a href="/admin/student/delete/${student.id}"
                                   class="btn btn-sm btn-outline-danger px-3"
                                   onclick="return confirm('Delete this student profile?')">

                                    <i class="bi bi-trash"></i> Delete

                                </a>

                            </td>

                        </tr>
                    `;

                });

            });

    });

}


/* ===========================
   COMPLAINT LIVE SEARCH
=========================== */

const complaintSearch = document.getElementById("searchComplaint");
const complaintTable = document.getElementById("complaintTable");

if (complaintSearch && complaintTable) {

    complaintSearch.addEventListener("keyup", function () {

        let query = this.value;

        fetch(`/admin/complaints/search?q=${query}`)

            .then(response => response.json())

            .then(data => {

                complaintTable.innerHTML = "";

                if (data.length === 0) {

                    complaintTable.innerHTML = `
                        <tr>
                            <td colspan="7" class="text-center py-5">
                                No complaints found
                            </td>
                        </tr>
                    `;

                    return;
                }

                data.forEach(c => {

                    let badge = "";

                    if (c.status === "Pending") {

                        badge = `<span class="badge bg-warning">Pending</span>`;

                    }
                    else if (c.status === "Resolved") {

                        badge = `<span class="badge bg-success">Resolved</span>`;

                    }
                    else {

                        badge = `<span class="badge bg-info">In Progress</span>`;

                    }

                    complaintTable.innerHTML += `

                        <tr>

                            <td>#${c.id}</td>

                            <td>${c.student}</td>

                            <td>
                                <span class="badge bg-secondary">
                                    ${c.category}
                                </span>
                            </td>

                            <td>${c.title}</td>

                            <td>${badge}</td>

                            <td>${c.date}</td>

                            <td class="text-end">

                                <a href="/admin/complaint/${c.id}"
                                   class="btn btn-sm btn-outline-primary">

                                    <i class="bi bi-eye"></i> View

                                </a>

                            </td>

                        </tr>

                    `;

                });

            });

    });

}