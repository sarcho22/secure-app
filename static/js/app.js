document.addEventListener("DOMContentLoaded", () => {
    setupLoginForm();
    setupRegisterForm();
    setupForgotPasswordForm();
    setupResetPasswordForm();
    setupDashboard();
    setupDocumentPage();
    setupAdminDashboard();
});

/* =========================
   Setup functions
========================= */

function setupLoginForm() {
    const loginForm = document.getElementById("loginForm");
    if (!loginForm) return;

    const messageBox = document.getElementById("error");
    const params = new URLSearchParams(window.location.search);
    if (params.get("registered") === "1") {
        showMessage(messageBox, "Registration successful. Please log in.", "success");

        window.history.replaceState({}, document.title, "/login-page");
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = getValue("username");
        const password = getValue("password");

        clearMessage(messageBox);

        try {
            const res = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ username, password })
            });

            const data = await parseJsonSafely(res);

            if (res.ok) {
                if (data.role === "admin") {
                    window.location.href = "/admin/dashboard";
                } else {
                    window.location.href = "/dashboard";
                }
            } else {
                showMessage(messageBox, data.error || "Login failed.", "error");
            }
        } catch (error) {
            showMessage(messageBox, "Server error. Please try again.", "error");
        }
    });
}

function setupRegisterForm() {
    const registerForm = document.getElementById("registerForm");
    if (!registerForm) return;

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = getValue("username");
        const email = getValue("email");
        const password = getValue("password");
        const confirm_password = getValue("confirm");
        const messageBox = getMessageElement(["error", "registerMessage"]);

        clearMessage(messageBox);

        if (password !== confirm_password) {
            showMessage(messageBox, "Passwords do not match.", "error");
            return;
        }

        try {
            const res = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    confirm_password
                })
            });

            const data = await parseJsonSafely(res);

            if (res.ok) {
                window.location.href = "/login-page?registered=1";
                return;
            } else {
                showMessage(messageBox, data.error || "Registration failed.", "error");
            }
        } catch (error) {
            showMessage(messageBox, "Server error. Please try again.", "error");
        }
    });
}

function setupForgotPasswordForm() {
    const forgotForm = document.getElementById("forgotPasswordForm");
    if (!forgotForm) return;

    forgotForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const identifier =
            getValue("forgotIdentifier") ||
            getValue("username") ||
            getValue("email");

        const messageBox = getMessageElement(["forgotMessage", "error"]);

        clearMessage(messageBox);

        if (!identifier) {
            showMessage(messageBox, "Please enter your email.", "error");
            return;
        }

        try {
            const res = await fetch("/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: identifier })
            });

            const data = await parseJsonSafely(res);

            if (res.ok) {
                showMessage(
                    messageBox,
                    data.message || "Password reset request submitted.",
                    "success"
                );
                forgotForm.reset();
            } else {
                showMessage(
                    messageBox,
                    data.error || "Could not process password reset request.",
                    "error"
                );
            }
        } catch (error) {
            showMessage(messageBox, "Server error. Please try again.", "error");
        }
    });
}

function setupResetPasswordForm() {
    const resetForm = document.getElementById("resetPasswordForm");
    if (!resetForm) return;

    resetForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const token = getValue("resetToken");
        const newPassword = getValue("newPassword");
        const confirmPassword = getValue("confirmPassword");
        const messageBox = getMessageElement(["resetMessage", "error"]);

        clearMessage(messageBox);

        if (!token) {
            showMessage(messageBox, "Missing reset token.", "error");
            return;
        }

        if (!newPassword || !confirmPassword) {
            showMessage(messageBox, "Please fill in both password fields.", "error");
            return;
        }

        if (newPassword !== confirmPassword) {
            showMessage(messageBox, "Passwords do not match.", "error");
            return;
        }

        try {
            const res = await fetch("/reset-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    token: token,
                    new_password: newPassword
                })
            });

            const data = await parseJsonSafely(res);

            if (res.ok) {
                showMessage(
                    messageBox,
                    data.message || "Password reset successful.",
                    "success"
                );

                setTimeout(() => {
                    window.location.href = "/login-page";
                }, 1500);
            } else {
                showMessage(
                    messageBox,
                    data.error || "Password reset failed.",
                    "error"
                );
            }
        } catch (error) {
            showMessage(messageBox, "Server error. Please try again.", "error");
        }
    });
}

function setupDashboard() {
    const welcomeText = document.getElementById("welcomeText");
    const logoutBtn = document.getElementById("logoutBtn");
    const docsBtn = document.getElementById("docsBtn");

    if (welcomeText) {
        loadCurrentUser();
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }

    if (docsBtn) {
        docsBtn.addEventListener("click", () => {
            window.location.href = "/documents-page";
        });
    }
}

function setupAdminDashboard() {
    const usersTableBody = document.getElementById("usersTableBody");
    const documentsTableBody = document.getElementById("documentsTableBody");
    const adminLogoutBtn = document.getElementById("adminLogoutBtn");
    const viewLogsBtn = document.getElementById("viewLogsBtn");
    const viewAccessLogsBtn = document.getElementById("viewAccessLogsBtn");

    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener("click", logout);
    }

    if (viewLogsBtn) {
        viewLogsBtn.addEventListener("click", () => {
            window.location.href = "/admin/logs";
        });
    }

    if (viewAccessLogsBtn) {
        viewAccessLogsBtn.addEventListener("click", () => {
            window.location.href = "/admin/access-logs";
        });
    }

    if (!usersTableBody || !documentsTableBody) return;

    loadAdminDashboard();
}

function setupDocumentPage() {
    const uploadForm = document.getElementById("uploadForm");
    const docList = document.getElementById("docList");

    if (docList) {
        loadDocuments();
        setupDocumentActions();
    }

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById("fileInput");
            const uploadMessage = getMessageElement(["uploadMessage", "error"]);
            clearMessage(uploadMessage);

            if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                showMessage(uploadMessage, "Please select a file.", "error");
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append("file", file);

            try {
                const res = await fetch("/upload", {
                    method: "POST",
                    credentials: "include",
                    body: formData
                });

                const data = await parseJsonSafely(res);

                if (res.ok) {
                    uploadForm.reset();
                    showMessage(
                        uploadMessage,
                        data.message || "Upload successful.",
                        "success"
                    );
                    loadDocuments();
                } else {
                    showMessage(
                        uploadMessage,
                        data.error || "Upload failed.",
                        "error"
                    );
                }
            } catch (error) {
                showMessage(uploadMessage, "Server error. Please try again.", "error");
            }
        });
    }
}

/* =========================
   Dashboard functions
========================= */

async function loadCurrentUser() {
    const welcomeText = document.getElementById("welcomeText");
    const messageBox = getMessageElement(["error", "dashboardMessage"]);

    try {
        const res = await fetch("/me", {
            credentials: "include"
        });

        const data = await parseJsonSafely(res);

        if (res.ok) {
            welcomeText.textContent = `Welcome, ${data.username}! Your role is: ${data.role}`;
            clearMessage(messageBox);
        } else {
            welcomeText.textContent = "Could not load user info.";
            showMessage(messageBox, data.error || "Authentication required.", "error");
        }
    } catch (error) {
        if (welcomeText) {
            welcomeText.textContent = "Could not load user info.";
        }
        showMessage(messageBox, "Server error. Please try again.", "error");
    }
}

async function logout() {
    try {
        await fetch("/logout", {
            method: "POST",
            credentials: "include"
        });
    } catch (error) {
        // still redirect
    }

    window.location.href = "/login-page";
}

/* =========================
   Document functions
========================= */
/* =========================
   Admin dashboard functions
========================= */

async function loadAdminDashboard() {
    const usersTableBody = document.getElementById("usersTableBody");
    const documentsTableBody = document.getElementById("documentsTableBody");
    const messageBox = document.getElementById("message");

    if (!usersTableBody || !documentsTableBody) return;

    usersTableBody.innerHTML = "";
    documentsTableBody.innerHTML = "";
    clearMessage(messageBox);

    try {
        const res = await fetch("/admin/data", {
            method: "GET",
            credentials: "include"
        });

        const data = await parseJsonSafely(res);

        if (!res.ok) {
            showMessage(messageBox, data.error || "Could not load admin data.", "error");
            return;
        }

        const users = data.users || [];
        const documents = data.documents || [];

        if (users.length === 0) {
            usersTableBody.innerHTML = `
                <tr>
                    <td colspan="3">No users found.</td>
                </tr>
            `;
        } else {
            users.forEach((user) => {
                const row = document.createElement("tr");

                const usernameCell = document.createElement("td");
                usernameCell.textContent = user.username;

                const roleCell = document.createElement("td");
                roleCell.textContent = user.role;

                const actionsCell = document.createElement("td");
                const actionsDiv = document.createElement("div");
                actionsDiv.className = "admin-actions";

                if (user.role === "guest") {
                    const btn = document.createElement("button");
                    btn.className = "btn";
                    btn.type = "button";
                    btn.textContent = "Promote to User";
                    btn.addEventListener("click", () => promoteUser(user.username));
                    actionsDiv.appendChild(btn);
                } else if (user.role === "user") {
                    const btn = document.createElement("button");
                    btn.className = "btn";
                    btn.type = "button";
                    btn.textContent = "Demote to Guest";
                    btn.addEventListener("click", () => demoteUser(user.username));
                    actionsDiv.appendChild(btn);
                } else {
                    actionsDiv.textContent = "Admin";
                }

                actionsCell.appendChild(actionsDiv);

                row.appendChild(usernameCell);
                row.appendChild(roleCell);
                row.appendChild(actionsCell);

                usersTableBody.appendChild(row);
            });
        }

        if (documents.length === 0) {
            documentsTableBody.innerHTML = `
                <tr>
                    <td colspan="4">No documents found.</td>
                </tr>
            `;
        } else {
            documents.forEach((doc) => {
                const row = document.createElement("tr");

                const titleCell = document.createElement("td");
                titleCell.textContent = doc.title || doc.filename || "Untitled";

                const ownerCell = document.createElement("td");
                ownerCell.textContent = doc.owner || "unknown";

                const visibilityCell = document.createElement("td");
                visibilityCell.textContent = doc.visibility || "unknown";

                const actionsCell = document.createElement("td");
                const actionsDiv = document.createElement("div");
                actionsDiv.className = "admin-actions";

                const downloadBtn = document.createElement("button");
                downloadBtn.className = "btn";
                downloadBtn.type = "button";
                downloadBtn.textContent = "Download";
                downloadBtn.addEventListener("click", () => downloadDoc(doc.doc_id));

                actionsDiv.appendChild(downloadBtn);
                actionsCell.appendChild(actionsDiv);

                row.appendChild(titleCell);
                row.appendChild(ownerCell);
                row.appendChild(visibilityCell);
                row.appendChild(actionsCell);

                documentsTableBody.appendChild(row);
            });
        }
    } catch (error) {
        showMessage(messageBox, "Server error. Could not load admin data.", "error");
    }
}

function setupDocumentActions() {
    const docList = document.getElementById("docList");
    if (!docList) return;

    docList.addEventListener("click", async (e) => {
        const button = e.target.closest("button[data-action]");
        if (!button) return;

        const action = button.dataset.action;
        const docId = button.dataset.docId;

        if (!docId) return;

        if (action === "download") {
            await downloadDocument(docId);
        } else if (action === "replace") {
            await replaceDocumentPrompt(docId);
        } else if (action === "delete") {
            await deleteDocument(docId);
        } else if (action === "toggle-share-panel") {
            await toggleSharePanel(docId);
        } else if (action === "submit-share") {
            await submitShare(docId);
        } else if (action === "unshare") {
            const targetUsername = button.dataset.targetUsername;
            if (targetUsername) {
                await unshareDocument(docId, targetUsername);
            }
        }
    });
}

async function loadDocuments() {
    const docList = document.getElementById("docList");
    if (!docList) return;

    try {
        const res = await fetch("/documents", {
            credentials: "include"
        });

        const data = await parseJsonSafely(res);
        docList.innerHTML = "";

        if (!res.ok) {
            docList.innerHTML = "<p>Could not load documents.</p>";
            return;
        }

        if (!data.documents || data.documents.length === 0) {
            docList.innerHTML = "<p>No documents yet.</p>";
            return;
        }

        data.documents.forEach((doc) => {
            const card = document.createElement("div");
            card.className = "doc-card";

            card.innerHTML = `
                <div class="doc-title">${escapeHtml(doc.filename || "Untitled file")}</div>
                <div class="doc-meta">Version: ${escapeHtml(String(doc.version ?? 1))}</div>

                <div class="doc-actions">
                    <button class="btn" type="button" data-action="download" data-doc-id="${escapeAttribute(doc.doc_id)}">Download</button>
                    <button class="btn" type="button" data-action="replace" data-doc-id="${escapeAttribute(doc.doc_id)}">Replace</button>
                    <button class="btn" type="button" data-action="delete" data-doc-id="${escapeAttribute(doc.doc_id)}">Delete</button>
                    <button class="btn" type="button" data-action="toggle-share-panel" data-doc-id="${escapeAttribute(doc.doc_id)}">Share / Access</button>
                </div>

                <div class="share-panel" id="share-panel-${escapeAttribute(doc.doc_id)}" style="display:none;">
                    <div class="share-form">
                        <input
                            type="text"
                            class="input share-username"
                            id="share-username-${escapeAttribute(doc.doc_id)}"
                            placeholder="Username"
                        />

                        <select
                            class="input share-role"
                            id="share-role-${escapeAttribute(doc.doc_id)}"
                        >
                            <option value="viewer">viewer</option>
                            <option value="editor">editor</option>
                        </select>

                        <button
                            class="btn"
                            type="button"
                            data-action="submit-share"
                            data-doc-id="${escapeAttribute(doc.doc_id)}"
                        >
                            Share
                        </button>
                    </div>

                    <div
                        class="share-list"
                        id="share-list-${escapeAttribute(doc.doc_id)}"
                        style="margin-top:10px;"
                    >
                        <p>Access list not loaded.</p>
                    </div>
                </div>
            `;

            docList.appendChild(card);
        });
    } catch (error) {
        docList.innerHTML = "<p>Could not load documents.</p>";
    }
}

async function downloadDocument(docId) {
    try {
        const res = await fetch(`/download/${encodeURIComponent(docId)}`, {
            credentials: "include"
        });

        if (!res.ok) {
            let errorMessage = "Download failed.";

            try {
                const data = await res.json();
                errorMessage = data.error || errorMessage;
            } catch (err) {
                // ignore parse failure
            }

            alert(errorMessage);
            return;
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;

        const disposition = res.headers.get("Content-Disposition");
        let filename = "downloaded_file";

        if (disposition && disposition.includes("filename=")) {
            filename = disposition.split("filename=")[1].replace(/"/g, "");
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert("Download failed.");
    }
}

async function deleteDocument(docId) {
    const confirmed = window.confirm("Are you sure you want to delete this document?");
    if (!confirmed) return;

    try {
        const res = await fetch(`/documents/${encodeURIComponent(docId)}`, {
            method: "DELETE",
            credentials: "include"
        });

        const data = await parseJsonSafely(res);

        if (res.ok) {
            loadDocuments();
        } else {
            alert(data.error || "Delete failed.");
        }
    } catch (error) {
        alert("Delete failed.");
    }
}

async function replaceDocumentPrompt(docId) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";

    fileInput.onchange = async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("doc_id", docId);

        try {
            const res = await fetch("/replace", {
                method: "POST",
                credentials: "include",
                body: formData
            });

            const data = await parseJsonSafely(res);

            if (res.ok) {
                loadDocuments();
            } else {
                alert(data.error || "Replace failed.");
            }
        } catch (error) {
            alert("Replace failed.");
        }
    };

    fileInput.click();
}

/* =========================
   Helpers
========================= */

function getValue(id) {
    const element = document.getElementById(id);
    return element ? element.value.trim() : "";
}

function getMessageElement(idOptions) {
    for (const id of idOptions) {
        const element = document.getElementById(id);
        if (element) return element;
    }
    return null;
}

function showMessage(element, text, type = "error") {
    if (!element) return;

    element.textContent = text;

    if (element.classList) {
        element.classList.remove("error", "success");
        if (element.classList.contains("message")) {
            element.classList.add(type);
        } else if (element.id === "error" || element.id === "uploadMessage") {
            if (type === "success") {
                element.style.color = "green";
            } else {
                element.style.color = "red";
            }
        }
    }
}

function clearMessage(element) {
    if (!element) return;

    element.textContent = "";

    if (element.classList) {
        element.classList.remove("error", "success");
    }

    if (element.id === "error" || element.id === "uploadMessage") {
        element.style.color = "";
    }
}

async function parseJsonSafely(response) {
    try {
        return await response.json();
    } catch (error) {
        return {};
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value);
}
function closeAllSharePanels() {
    document.querySelectorAll(".share-panel").forEach(panel => {
        panel.style.display = "none";
    });
}

async function toggleSharePanel(docId) {
    const panel = document.getElementById(`share-panel-${docId}`);
    if (!panel) return;

    const isOpen = panel.style.display === "block";

    closeAllSharePanels();

    if (isOpen) return;

    panel.style.display = "block";
    await loadShareList(docId);
}

async function loadShareList(docId) {
    const list = document.getElementById(`share-list-${docId}`);
    if (!list) return;

    list.innerHTML = "<p>Loading access list...</p>";

    try {
        const res = await fetch(`/shares/${encodeURIComponent(docId)}`, {
            credentials: "include"
        });

        const data = await parseJsonSafely(res);

        if (!res.ok) {
            list.innerHTML = `<p>${escapeHtml(data.error || "Could not load access list.")}</p>`;
            return;
        }

        if (!data.shares || data.shares.length === 0) {
            list.innerHTML = "<p>No shared users.</p>";
            return;
        }

        list.innerHTML = data.shares.map((entry) => `
            <div class="doc-card" style="margin-top:8px;">
                <div class="doc-title">${escapeHtml(entry.username)}</div>
                <div class="doc-meta">Role: ${escapeHtml(entry.role)}</div>
                <div class="doc-actions">
                    <button
                        class="btn"
                        type="button"
                        data-action="unshare"
                        data-doc-id="${escapeAttribute(docId)}"
                        data-target-username="${escapeAttribute(entry.username)}"
                    >
                        Unshare
                    </button>
                </div>
            </div>
        `).join("");
    } catch (error) {
        list.innerHTML = "<p>Could not load access list.</p>";
    }
}

async function submitShare(docId) {
    const usernameInput = document.getElementById(`share-username-${docId}`);
    const roleInput = document.getElementById(`share-role-${docId}`);

    if (!usernameInput || !roleInput) return;

    const targetUsername = usernameInput.value.trim();
    const role = roleInput.value.trim().toLowerCase();

    if (!targetUsername) {
        alert("Please enter a username.");
        return;
    }

    try {
        const res = await fetch("/share", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
                doc_id: docId,
                target_username: targetUsername,
                role: role
            })
        });

        const data = await parseJsonSafely(res);

        if (res.ok) {
            usernameInput.value = "";
            roleInput.value = "viewer";
            await loadShareList(docId);
        } else {
            alert(data.error || "Share failed.");
        }
    } catch (error) {
        alert("Share failed.");
    }
}

async function unshareDocument(docId, targetUsername) {
    const confirmed = window.confirm(`Remove access for ${targetUsername}?`);
    if (!confirmed) return;

    try {
        const res = await fetch("/unshare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
                doc_id: docId,
                target_username: targetUsername
            })
        });

        const data = await parseJsonSafely(res);

        if (res.ok) {
            await loadShareList(docId);
        } else {
            alert(data.error || "Unshare failed.");
        }
    } catch (error) {
        alert("Unshare failed.");
    }
}

async function promoteUser(username) {
    const messageBox = getMessageElement(["message"]);
    clearMessage(messageBox);

    try {
        const response = await fetch("/admin/promote", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({ target_username: username })
        });

        const result = await parseJsonSafely(response);

        if (response.ok) {
            showMessage(messageBox, result.message || "User promoted successfully.", "success");
            await loadAdminDashboard();
        } else {
            showMessage(messageBox, result.error || "Promotion failed.", "error");
        }
    } catch (error) {
        showMessage(messageBox, "Server error. Promotion failed.", "error");
    }
}

async function demoteUser(username) {
    const messageBox = getMessageElement(["message"]);
    clearMessage(messageBox);

    try {
        const response = await fetch("/admin/demote", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({ target_username: username })
        });

        const result = await parseJsonSafely(response);

        if (response.ok) {
            showMessage(messageBox, result.message || "User demoted successfully.", "success");
            await loadAdminDashboard();
        } else {
            showMessage(messageBox, result.error || "Demotion failed.", "error");
        }
    } catch (error) {
        showMessage(messageBox, "Server error. Demotion failed.", "error");
    }
}

function downloadDoc(docId) {
    window.location.href = `/download/${encodeURIComponent(docId)}`;
}
