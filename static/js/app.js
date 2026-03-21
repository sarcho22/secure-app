document.addEventListener("DOMContentLoaded", () => {
    // ---------------- LOGIN ----------------
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

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
                const error = document.getElementById("error");
                if (error) error.innerText = data.error;
            }
        });
    }

    // ---------------- REGISTER ----------------
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const confirm_password = document.getElementById("confirm").value;

            const res = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password, confirm_password })
            });

            const data = await res.json();

            if (res.ok) {
                window.location.href = "/login-page";
            } else {
                const error = document.getElementById("error");
                if (error) error.innerText = data.error;
            }
        });
    }

    // ---------------- UPLOAD DOCUMENT ----------------
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const filename = document.getElementById("filename").value;
            const content = document.getElementById("content").value;
            const message = document.getElementById("uploadMessage");

            const res = await fetch("/upload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ filename, content })
            });

            const data = await res.json();

            if (res.ok) {
                if (message) {
                    message.textContent = "Upload successful";
                    message.className = "message success";
                }
                uploadForm.reset();
                loadDocuments();
            } else {
                if (message) {
                    message.textContent = data.error || "Upload failed";
                    message.className = "message error";
                }
            }
        });
    }

    // ---------------- PAGE-SPECIFIC LOADERS ----------------
    if (document.getElementById("docList")) {
        loadDocuments();
    }

    if (document.getElementById("currentUserDisplay")) {
        loadCurrentUser();
    }
});


// ---------------- LOGOUT ----------------
async function logout() {
    await fetch("/logout", {
        method: "POST",
        credentials: "include"
    });

    window.location.href = "/login-page";
}


// ---------------- CURRENT USER ----------------
async function loadCurrentUser() {
    const display = document.getElementById("currentUserDisplay");
    if (!display) return;

    const res = await fetch("/me", {
        credentials: "include"
    });

    const data = await res.json();

    if (res.ok) {
        display.textContent = `${data.username} • ${data.role}`;
    } else {
        display.textContent = "Not logged in";
    }
}


// ---------------- DOCUMENT LIST ----------------
async function loadDocuments() {
    const list = document.getElementById("docList");
    if (!list) return;

    const res = await fetch("/documents", {
        credentials: "include"
    });

    const data = await res.json();
    list.innerHTML = "";

    if (!res.ok) {
        list.innerHTML = `<div class="empty-state">Could not load documents.</div>`;
        return;
    }

    if (!data.documents || data.documents.length === 0) {
        list.innerHTML = `<div class="empty-state">No documents yet.</div>`;
        return;
    }

    data.documents.forEach(doc => {
        const card = document.createElement("div");
        card.className = "document-card";

        card.innerHTML = `
            <h3>${doc.filename}</h3>
            <div class="document-meta">
                <div><strong>Owner:</strong> ${doc.owner}</div>
                <div><strong>Version:</strong> ${doc.version}</div>
            </div>
            <div class="document-actions">
                <button type="button" onclick="downloadDoc('${doc.doc_id}')">Download</button>
                <button type="button" class="danger" onclick="deleteDoc('${doc.doc_id}')">Delete</button>
            </div>
        `;

        list.appendChild(card);
    });
}


// ---------------- DOWNLOAD DOCUMENT ----------------
async function downloadDoc(docId) {
    const res = await fetch(`/download/${docId}`, {
        credentials: "include"
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.error || "Download failed");
        return;
    }

    alert(`Filename: ${data.filename}\n\nContent:\n${data.content}`);
}


// ---------------- DELETE DOCUMENT ----------------
async function deleteDoc(docId) {
    const res = await fetch(`/documents/${docId}`, {
        method: "DELETE",
        credentials: "include"
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.error || "Delete failed");
        return;
    }

    loadDocuments();
}