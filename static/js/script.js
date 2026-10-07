let currentRole = "";
let currentToken = localStorage.getItem("token") || "";


/* =========================
   LOGIN SECTION
========================= */

function showLogin(role) {

    currentRole = role;

    const section = document.getElementById("login-section");

    if (!section) {
        console.error("login-section not found!");
        return;
    }

    let title = "";

    if (role === "applicant") {
        title = "Applicant Login";
    } else if (role === "admin") {
        title = "Administrator Login";
    } else {
        title = "Police Officer Login";
    }

    section.innerHTML = `
        <div class="login-box">

            <h2>${title}</h2>

            <input
                type="text"
                id="username"
                placeholder="Username"
            >

            <input
                type="password"
                id="password"
                placeholder="Password"
            >

            <button onclick="login('${role}')">
                Login
            </button>

            ${
                role === "applicant"
                ? `
                    <button onclick="showRegister()">
                        Register
                    </button>
                `
                : ""
            }

            <p id="login-message"></p>

        </div>
    `;
}


/* =========================
   LOGIN
========================= */

async function login(role) {

    const usernameElement =
        document.getElementById("username");

    const passwordElement =
        document.getElementById("password");

    const message =
        document.getElementById("login-message");

    if (!usernameElement || !passwordElement) {
        console.error("Login fields not found!");
        return;
    }

    const username = usernameElement.value.trim();
    const password = passwordElement.value;

    let url = "";

    if (role === "applicant") {
        url = "/api/applicants/login";
    } else if (role === "admin") {
        url = "/api/admin/login";
    } else if (role === "police") {
        url = "/api/police/login";
    }

    try {

        console.log("Sending login request to:", url);

        const response = await fetch(url, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                user_name: username,
                password: password
            })
        });

        console.log(
            "Server response:",
            response.status
        );

        const text = await response.text();

        console.log(
            "Server data:",
            text
        );

        let data;

        try {
            data = JSON.parse(text);
        } catch (error) {

            if (message) {
                message.textContent =
                    "Invalid server response.";
            }

            return;
        }

        if (response.ok) {

            currentToken = data.token;
            currentRole = role;

            localStorage.setItem(
                "token",
                currentToken
            );

            localStorage.setItem(
                "role",
                role
            );

            if (role === "applicant") {

                showApplicantDashboard();

            } else if (role === "admin") {

                showAdminDashboard();

            } else if (role === "police") {

                showPoliceDashboard();
            }

        } else {

            if (message) {
                message.textContent =
                    data.error || "Login failed!";
            }
        }

    } catch (error) {

        console.error(
            "LOGIN ERROR:",
            error
        );

        if (message) {
            message.textContent =
                "Cannot connect to Flask server.";
        }
    }
}


/* =========================
   APPLICANT REGISTRATION
========================= */

function showRegister() {

    const section =
        document.getElementById("login-section");

    if (!section) return;

    section.innerHTML = `

        <div class="login-box">

            <h2>Applicant Registration</h2>

            <input
                type="text"
                id="reg-name"
                placeholder="Full Name"
            >

            <input
                type="text"
                id="reg-father-name"
                placeholder="Father Name"
            >

            <input
                type="date"
                id="reg-dob"
            >

            <input
                type="text"
                id="reg-address"
                placeholder="Address"
            >

            <input
                type="email"
                id="reg-email"
                placeholder="Email"
            >

            <input
                type="text"
                id="reg-phone"
                placeholder="Phone Number"
            >

            <input
                type="text"
                id="reg-username"
                placeholder="Username"
            >

            <input
                type="password"
                id="reg-password"
                placeholder="Password"
            >

            <button onclick="registerApplicant()">
                Register
            </button>

            <button onclick="showLogin('applicant')">
                Back to Login
            </button>

            <p id="register-message"></p>

        </div>
    `;
}


async function registerApplicant() {

    const data = {

        name:
            document.getElementById("reg-name").value,

        father_name:
            document.getElementById("reg-father-name").value,

        dob:
            document.getElementById("reg-dob").value,

        address:
            document.getElementById("reg-address").value,

        email:
            document.getElementById("reg-email").value,

        phone_no:
            document.getElementById("reg-phone").value,

        user_name:
            document.getElementById("reg-username").value,

        password:
            document.getElementById("reg-password").value
    };

    try {

        const response = await fetch(
            "/api/applicants/register",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify(data)
            }
        );

        const result =
            await response.json();

        const message =
            document.getElementById(
                "register-message"
            );

        if (response.ok) {

            message.textContent =
                "Registration successful! You can now login.";

        } else {

            message.textContent =
                result.error ||
                "Registration failed!";
        }

    } catch (error) {

        console.error(
            "REGISTRATION ERROR:",
            error
        );

        const message =
            document.getElementById(
                "register-message"
            );

        if (message) {
            message.textContent =
                "Server connection error!";
        }
    }
}


/* =========================
   APPLICANT DASHBOARD
========================= */

function showApplicantDashboard() {

    let mainSection =
        document.getElementById("main-section");

    /*
       IMPORTANT FIX:
       If main-section does not exist,
       create it automatically.
    */

    if (!mainSection) {

        console.warn(
            "main-section not found. Creating it."
        );

        mainSection =
            document.createElement("div");

        mainSection.id =
            "main-section";

        document.body.appendChild(
            mainSection
        );
    }

    mainSection.innerHTML = `

        <div class="dashboard">

            <h2>Applicant Dashboard</h2>

            <div class="menu">

                <button onclick="applyPassport()">
                    Apply for Passport
                </button>

                <button onclick="showPayment()">
                    Pay Passport Fee
                </button>

                <button onclick="trackApplication()">
                    Track Application
                </button>

                <button onclick="receivePassport()">
                    Receive Passport
                </button>

                <button
                    class="logout"
                    onclick="logout()"
                >
                    Logout
                </button>

            </div>

            <div id="dashboard-content"></div>

        </div>
    `;
}


/* =========================
   APPLY PASSPORT
========================= */

async function applyPassport() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    try {

        const response = await fetch(
            "/api/applications",
            {
                method: "POST",

                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const data =
            await response.json();

        if (response.ok) {

            content.innerHTML = `

                <div class="result success">

                    <h3>Application Created!</h3>

                    <p>
                        Application ID:
                        <strong>
                            ${data.application_id}
                        </strong>
                    </p>

                    <p>
                        Status:
                        ${data.state}
                    </p>

                    <p>
                        Please proceed to payment.
                    </p>

                </div>
            `;

        } else {

            content.innerHTML =
                `<p class="error">
                    ${data.error || "Application failed!"}
                </p>`;
        }

    } catch (error) {

        console.error(
            "APPLICATION ERROR:",
            error
        );

        content.innerHTML =
            `<p class="error">
                Server connection error!
            </p>`;
    }
}


/* =========================
   PAYMENT
========================= */

function showPayment() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    content.innerHTML = `

        <div class="form-box">

            <h3>Passport Fee Payment</h3>

            <p>Fee: ₹1500</p>

            <input
                type="number"
                id="application-id"
                placeholder="Application ID"
            >

            <input
                type="text"
                id="card-number"
                placeholder="16 digit card number"
            >

            <button onclick="payFee()">
                Pay ₹1500
            </button>

            <p id="payment-message"></p>

        </div>
    `;
}


async function payFee() {

    const applicationId =
        document.getElementById(
            "application-id"
        ).value;

    const card =
        document.getElementById(
            "card-number"
        ).value;

    try {

        const response = await fetch(
            `/api/applications/${applicationId}/pay`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    "Authorization":
                        "Bearer " + currentToken
                },

                body: JSON.stringify({
                    card: card
                })
            }
        );

        const data =
            await response.json();

        const message =
            document.getElementById(
                "payment-message"
            );

        if (message) {

            message.textContent =
                data.success
                ? "Payment successful! Application submitted."
                : (
                    data.error ||
                    "Payment failed. Please retry."
                );
        }

    } catch (error) {

        console.error(
            "PAYMENT ERROR:",
            error
        );

        const message =
            document.getElementById(
                "payment-message"
            );

        if (message) {
            message.textContent =
                "Server connection error!";
        }
    }
}


/* =========================
   TRACK APPLICATION
========================= */

async function trackApplication() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    try {

        const response = await fetch(
            "/api/applications",
            {
                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const applications =
            await response.json();

        if (!applications.length) {

            content.innerHTML =
                "<p>No applications found.</p>";

            return;
        }

        content.innerHTML = `

            <div class="result">

                <h3>My Applications</h3>

                ${applications.map(app => `

                    <div class="application-card">

                        <p>
                            <strong>
                                Application ID:
                            </strong>
                            ${app.application_id}
                        </p>

                        <p>
                            <strong>Status:</strong>
                            ${app.state}
                        </p>

                        <p>
                            <strong>
                                Document Status:
                            </strong>
                            ${app.document_status || "Pending"}
                        </p>

                        <p>
                            <strong>
                                Passport Number:
                            </strong>
                            ${app.passport_number || "Not generated"}
                        </p>

                    </div>

                `).join("")}

            </div>
        `;

    } catch (error) {

        console.error(
            "TRACK ERROR:",
            error
        );

        content.innerHTML =
            `<p class="error">
                Server connection error!
            </p>`;
    }
}


/* =========================
   RECEIVE PASSPORT
========================= */

async function receivePassport() {

    const applicationId =
        prompt("Enter Application ID:");

    if (!applicationId) return;

    try {

        const response = await fetch(
            `/api/applications/${applicationId}/receive`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const data =
            await response.json();

        const content =
            document.getElementById(
                "dashboard-content"
            );

        if (!content) return;

        content.innerHTML =
            response.ok

            ? `
                <div class="result success">

                    <h3>
                        Passport Received!
                    </h3>

                    <p>
                        Status: ${data.state}
                    </p>

                </div>
            `

            : `
                <p class="error">
                    ${data.error || "Unable to receive passport."}
                </p>
            `;

    } catch (error) {

        console.error(
            "RECEIVE ERROR:",
            error
        );
    }
}


/* =========================
   ADMIN DASHBOARD
========================= */

function showAdminDashboard() {

    let mainSection =
        document.getElementById("main-section");

    if (!mainSection) {

        mainSection =
            document.createElement("div");

        mainSection.id =
            "main-section";

        document.body.appendChild(
            mainSection
        );
    }

    mainSection.innerHTML = `

        <div class="dashboard">

            <h2>Administrator Dashboard</h2>

            <div class="menu">

                <button onclick="adminApplications()">
                    View Applications
                </button>

                <button onclick="adminAccounts()">
                    Manage Accounts
                </button>

                <button
                    class="logout"
                    onclick="logout()"
                >
                    Logout
                </button>

            </div>

            <div id="dashboard-content"></div>

        </div>
    `;
}


/* =========================
   ADMIN APPLICATIONS
========================= */

async function adminApplications() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    try {

        const response = await fetch(
            "/api/admin/applications",
            {
                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const apps =
            await response.json();

        if (!apps.length) {

            content.innerHTML =
                "<p>No applications available.</p>";

            return;
        }

        content.innerHTML = `

            <h3>Applications</h3>

            ${apps.map(app => `

                <div class="application-card">

                    <p>
                        <strong>ID:</strong>
                        ${app.application_id}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        ${app.state}
                    </p>

                    <p>
                        <strong>Document:</strong>
                        ${app.document_status || "Pending"}
                    </p>

                    <button
                        onclick="adminVerify(${app.application_id})"
                    >
                        Verify
                    </button>

                    <button
                        onclick="adminForward(${app.application_id})"
                    >
                        Forward to Police
                    </button>

                    <button
                        onclick="adminDocumentStatus(${app.application_id})"
                    >
                        Approve Document
                    </button>

                    <button
                        onclick="generatePassport(${app.application_id})"
                    >
                        Generate Passport
                    </button>

                </div>

            `).join("")}

        `;

    } catch (error) {

        console.error(
            "ADMIN APPLICATION ERROR:",
            error
        );

        content.innerHTML =
            `<p class="error">
                Server connection error!
            </p>`;
    }
}


/* =========================
   ADMIN ACTIONS
========================= */

async function adminVerify(id) {

    await adminAction(
        `/api/admin/applications/${id}/verify`,
        "POST",
        {},
        "Application verified successfully!"
    );
}


async function adminForward(id) {

    await adminAction(
        `/api/admin/applications/${id}/forward`,
        "POST",
        {},
        "Application forwarded to Police!"
    );
}


async function adminDocumentStatus(id) {

    await adminAction(
        `/api/admin/applications/${id}/document-status`,
        "POST",
        {},
        "Document approved!"
    );
}


async function generatePassport(id) {

    await adminAction(
        `/api/admin/applications/${id}/generate`,
        "POST",
        {},
        "Passport generated successfully!"
    );
}


async function adminAction(
    url,
    method,
    body,
    successMessage
) {

    try {

        const response = await fetch(
            url,
            {
                method: method,

                headers: {
                    "Content-Type":
                        "application/json",

                    "Authorization":
                        "Bearer " + currentToken
                },

                body: JSON.stringify(body)
            }
        );

        const data =
            await response.json();

        const content =
            document.getElementById(
                "dashboard-content"
            );

        if (!content) return;

        content.innerHTML =
            response.ok

            ? `
                <div class="result success">

                    <h3>
                        ${successMessage}
                    </h3>

                    <button
                        onclick="adminApplications()"
                    >
                        Refresh Applications
                    </button>

                </div>
            `

            : `
                <div class="result error">

                    ${
                        data.error ||
                        "Operation failed"
                    }

                </div>
            `;

    } catch (error) {

        console.error(
            "ADMIN ACTION ERROR:",
            error
        );

        const content =
            document.getElementById(
                "dashboard-content"
            );

        if (content) {

            content.innerHTML =
                `<p class="error">
                    Server connection error!
                </p>`;
        }
    }
}


/* =========================
   ADMIN ACCOUNTS
========================= */

async function adminAccounts() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    try {

        const response = await fetch(
            "/api/admin/accounts",
            {
                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const accounts =
            await response.json();

        content.innerHTML = `

            <h3>User Accounts</h3>

            ${accounts.map(account => `

                <div class="application-card">

                    <p>
                        <strong>Role:</strong>
                        ${account.role}
                    </p>

                    <p>
                        <strong>Username:</strong>
                        ${account.user_name}
                    </p>

                </div>

            `).join("")}

            <button onclick="adminApplications()">
                Back to Applications
            </button>
        `;

    } catch (error) {

        console.error(
            "ADMIN ACCOUNTS ERROR:",
            error
        );

        content.innerHTML =
            `<p class="error">
                Server connection error!
            </p>`;
    }
}


/* =========================
   POLICE DASHBOARD
========================= */

function showPoliceDashboard() {

    let mainSection =
        document.getElementById("main-section");

    if (!mainSection) {

        mainSection =
            document.createElement("div");

        mainSection.id =
            "main-section";

        document.body.appendChild(
            mainSection
        );
    }

    mainSection.innerHTML = `

        <div class="dashboard">

            <h2>
                Police Verification Dashboard
            </h2>

            <div class="menu">

                <button onclick="policeRequests()">
                    Verification Requests
                </button>

                <button
                    class="logout"
                    onclick="logout()"
                >
                    Logout
                </button>

            </div>

            <div id="dashboard-content"></div>

        </div>
    `;
}


/* =========================
   POLICE REQUESTS
========================= */

async function policeRequests() {

    const content =
        document.getElementById(
            "dashboard-content"
        );

    if (!content) return;

    try {

        const response = await fetch(
            "/api/police/requests",
            {
                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const apps =
            await response.json();

        if (!apps.length) {

            content.innerHTML =
                "<p>No verification requests.</p>";

            return;
        }

        content.innerHTML = `

            <h3>Verification Requests</h3>

            ${apps.map(app => `

                <div class="application-card">

                    <p>
                        <strong>
                            Application ID:
                        </strong>
                        ${app.application_id}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        ${app.state}
                    </p>

                    <button
                        onclick="policeVerify(${app.application_id})"
                    >
                        Verify Applicant
                    </button>

                    <button
                        onclick="policeUpdate(${app.application_id})"
                    >
                        Update Verification
                    </button>

                </div>

            `).join("")}

        `;

    } catch (error) {

        console.error(
            "POLICE REQUEST ERROR:",
            error
        );

        content.innerHTML =
            `<p class="error">
                Server connection error!
            </p>`;
    }
}


/* =========================
   POLICE VERIFY
========================= */

async function policeVerify(id) {

    try {

        const response = await fetch(
            `/api/police/applications/${id}/verify`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const data =
            await response.json();

        const content =
            document.getElementById(
                "dashboard-content"
            );

        if (!content) return;

        content.innerHTML =
            response.ok

            ? `
                <div class="result success">

                    Applicant verification completed.

                    <br>

                    Result:
                    ${data.verified}

                    <br><br>

                    <button
                        onclick="policeRequests()"
                    >
                        Back
                    </button>

                </div>
            `

            : `
                <div class="result error">

                    ${data.error || "Verification failed."}

                </div>
            `;

    } catch (error) {

        console.error(
            "POLICE VERIFY ERROR:",
            error
        );
    }
}


/* =========================
   POLICE UPDATE
========================= */

async function policeUpdate(id) {

    try {

        const response = await fetch(
            `/api/police/applications/${id}/update`,
            {
                method: "POST",

                headers: {
                    "Authorization":
                        "Bearer " + currentToken
                }
            }
        );

        const data =
            await response.json();

        const content =
            document.getElementById(
                "dashboard-content"
            );

        if (!content) return;

        content.innerHTML =
            response.ok

            ? `
                <div class="result success">

                    Police verification status updated!

                    <br><br>

                    <button
                        onclick="policeRequests()"
                    >
                        Back
                    </button>

                </div>
            `

            : `
                <div class="result error">

                    ${data.error || "Update failed."}

                </div>
            `;

    } catch (error) {

        console.error(
            "POLICE UPDATE ERROR:",
            error
        );
    }
}


/* =========================
   LOGOUT
========================= */

function logout() {

    currentToken = "";
    currentRole = "";

    localStorage.removeItem("token");
    localStorage.removeItem("role");

    location.reload();
}
