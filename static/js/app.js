document.addEventListener("DOMContentLoaded", () => {

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
                document.getElementById("error").innerText = data.error;
            }
        });
    }

});


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
            document.getElementById("error").innerText = data.error;
        }
    });
}

async function logout() {
    await fetch("/logout", {
        method: "POST",
        credentials: "include"
    });

    window.location.href = "/login-page";
}

const uploadForm = document.getElementById("uploadForm");

if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const filename = document.getElementById("filename").value;
        const content = document.getElementById("content").value;

        await fetch("/upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ filename, content })
        });

        loadDocuments();
    });
}

async function loadDocuments() {
    const res = await fetch("/documents", { credentials: "include" });
    const data = await res.json();

    const list = document.getElementById("docList");
    list.innerHTML = "";

    data.documents.forEach(doc => {
        const li = document.createElement("li");
        li.innerText = doc.filename;
        list.appendChild(li);
    });
}

if (document.getElementById("docList")) {
    loadDocuments();
}

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

document.addEventListener("DOMContentLoaded", () => {
    loadCurrentUser();
});