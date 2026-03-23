document.addEventListener("DOMContentLoaded", () => {
    // login code
    const loginForm = document.getElementById("loginForm");

    if(loginForm) {
        loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const error = document.getElementById("error");

        const res = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (res.ok) {
            window.location.href = "/dashboard";
        } else {
            error.textContent = data.error;
        }
    });
    }

    // register code
    const registerForm = document.getElementById("registerForm");

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const confirm_password = document.getElementById("confirm").value;
            const error = document.getElementById("error");

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

            const data = await res.json();

            if (res.ok) {
                window.location.href = "/login-page";
            } else {
                error.textContent = data.error;
            }
        });
    }

    // dashboard code
    const welcomeText = document.getElementById("welcomeText");
    const logoutBtn = document.getElementById("logoutBtn");

    if (welcomeText) {
        loadCurrentUser();
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }

    // documents code
    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById("fileInput");
            const file = fileInput.files[0];

            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch("/upload", {
                method: "POST",
                credentials: "include",
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                loadDocuments();
            } else {
                alert(data.error);
            }
        });
    }

// dashboard functions
async function loadCurrentUser() {
    const welcomeText = document.getElementById("welcomeText");
    const error = document.getElementById("error");

    const res = await fetch("/me", {
        credentials: "include"
    });

    const data = await res.json();

    if (res.ok) {
        welcomeText.textContent = `Welcome, ${data.username}! Your role is: ${data.role}`;
        if (error) error.textContent = "";
    } else {
        welcomeText.textContent = "Could not load user info.";
        if (error) error.textContent = data.error || "Authentication required";
    }
}

async function logout() {
    await fetch("/logout", {
        method: "POST",
        credentials: "include"
    });

    window.location.href = "/login-page";
}

// document functions
async function loadDocuments() {
    const docList = document.getElementById("docList");
    if (!docList) return;

    const res = await fetch("/documents", {
        credentials: "include"
    });

    const data = await res.json();
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
            <div class="doc-title">${doc.filename}</div>
            <div class="doc-meta">Version: ${doc.version}</div>
            <div class="doc-actions">
                <button class="btn" type="button" onclick="downloadDocument('${doc.doc_id}')">Download</button>
                <button class="btn" type="button" onclick="replaceDocumentPrompt('${doc.doc_id}')">Replace</button>
                <button class="btn" type="button" onclick="deleteDocument('${doc.doc_id}')">Delete</button>
            </div>
        `;

        docList.appendChild(card);
    });
}

async function downloadDocument(docId) {
    const res = await fetch(`/download/${docId}`, {
        credentials: "include"
    });

    const data = await res.json();

    if (res.ok) {
        alert(`Filename: ${data.filename}\n\nContent:\n${data.content}`);
    } else {
        alert(data.error || "Download failed");
    }
}

async function deleteDocument(docId) {
    const res = await fetch(`/documents/${docId}`, {
        method: "DELETE",
        credentials: "include"
    });

    const data = await res.json();

    if (res.ok) {
        loadDocuments();
    } else {
        alert(data.error || "Delete failed");
    }
}

async function replaceDocumentPrompt(docId) {
    const newContent = prompt("Enter new document content:");
    if (newContent === null) return;

    const res = await fetch("/replace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
            doc_id: docId,
            content: newContent
        })
    });

    const data = await res.json();

    if (res.ok) {
        loadDocuments();
    } else {
        alert(data.error || "Replace failed");
    }
}