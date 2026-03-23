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
    const refreshUserBtn = document.getElementById("refreshUserBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    if (welcomeText) {
        loadCurrentUser();
    }

    if (refreshUserBtn) {
        refreshUserBtn.addEventListener("click", loadCurrentUser);
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }
});

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