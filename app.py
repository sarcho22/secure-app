from flask import Flask, redirect, request, jsonify, make_response, render_template, send_file
import config, io, os
from services.storage import save_json
from services.user_manager import register_user, authenticate_user
from services.session_manager import SessionManager
from services.document_manager import DocumentManager
from services.authz import require_auth, require_role, get_current_user

app = Flask(__name__)

app.config["SECRET_KEY"] = config.SECRET_KEY

session_manager = SessionManager()
document_manager = DocumentManager()

def ensure_app_files():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(config.DATA_DIR, "docs"), exist_ok=True)

    if not os.path.exists(config.USERS_FILE):
        save_json(config.USERS_FILE, {"users": []})

    if not os.path.exists(config.SESSIONS_FILE):
        save_json(config.SESSIONS_FILE, {"sessions": {}})

    if not os.path.exists(config.DOCUMENTS_FILE):
        save_json(config.DOCUMENTS_FILE, {"documents": []})

ensure_app_files()

# @app.route("/")
# def home():
    # return render_template("login.html")
@app.route("/")
def home():
    print("HOME ROUTE HIT", flush=True)
    return "Hello from Railway"

@app.errorhandler(Exception)
def handle_exception(e):
    print("UNHANDLED EXCEPTION:", repr(e), flush=True)
    return "Internal Server Error", 500

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
@require_auth
def dashboard():
    return render_template("dashboard.html")

@app.route("/documents-page")
@require_auth
def documents_page():
    return render_template("documents.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or request.form

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    result = register_user(username, email, password)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form

    username = data.get("username", "").strip()
    password = data.get("password", "")

    result = authenticate_user(username, password)
    if "error" in result:
        return jsonify(result), 401

    user = result["user"]
    token = session_manager.create_session(user["username"])

    response = make_response(jsonify({
        "success": True,
        "message": "Login successful",
        "username": user["username"],
        "role": user["role"]
    }))

    response.set_cookie(
        "session_token",
        token,
        httponly=True,
        secure=not app.debug,
        samesite="Lax",
        max_age=session_manager.timeout
    )

    return response


@app.route("/logout", methods=["POST"])
@require_auth
def logout():
    token = request.cookies.get("session_token")
    if token:
        session_manager.destroy_session(token)

    response = make_response(jsonify({
        "success": True,
        "message": "Logged out"
    }))
    response.delete_cookie("session_token")
    return response


@app.route("/me", methods=["GET"])
@require_auth
def me():
    user = get_current_user()
    return jsonify({
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    })

@app.route("/upload", methods=["POST"])
@require_auth
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    user = get_current_user()

    result = document_manager.upload_file(
        user["username"],
        file
    )

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 201


@app.route("/documents", methods=["GET"])
@require_auth
def list_documents():
    user = get_current_user()
    documents = document_manager.get_user_documents(user["username"])

    return jsonify({
        "documents": documents
    })

@app.route("/download/<doc_id>", methods=["GET"])
@require_auth
def download(doc_id):
    user = get_current_user()
    result = document_manager.get_file(user["username"], doc_id)

    if "error" in result:
        if result["error"] == "Document not found":
            return jsonify(result), 404
        return jsonify(result), 403

    file_bytes = result["data"]
    filename = result["filename"]

    return send_file(
        io.BytesIO(file_bytes),
        as_attachment=True,
        download_name=filename
    )

@app.route("/replace", methods=["POST"])
@require_auth
def replace_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    doc_id = request.form.get("doc_id", "").strip()

    user = get_current_user()
    result = document_manager.replace_file(user["username"], doc_id, file)

    if "error" in result:
        if result["error"] == "Document not found":
            return jsonify(result), 404
        return jsonify(result), 403

    return jsonify(result), 200

@app.route("/share", methods=["POST"])
@require_auth
def share_document():
    data = request.get_json(silent=True) or request.form

    doc_id = data.get("doc_id", "").strip()
    target_username = data.get("target_username", "").strip()
    role = data.get("role", "").strip()

    user = get_current_user()
    result = document_manager.share_document(user["username"], doc_id, target_username, role)

    if "error" in result:
        if result["error"] == "Document not found":
            return jsonify(result), 404
        if result["error"] == "Forbidden":
            return jsonify(result), 403
        return jsonify(result), 400

    return jsonify(result), 200


@app.route("/unshare", methods=["POST"])
@require_auth
def unshare_document():
    data = request.get_json(silent=True) or request.form

    doc_id = data.get("doc_id", "").strip()
    target_username = data.get("target_username", "").strip()

    user = get_current_user()
    result = document_manager.unshare_document(user["username"], doc_id, target_username)

    if "error" in result:
        if result["error"] == "Document not found":
            return jsonify(result), 404
        if result["error"] == "Forbidden":
            return jsonify(result), 403
        return jsonify(result), 400

    return jsonify(result), 200


@app.route("/shares/<doc_id>", methods=["GET"])
@require_auth
def list_shares(doc_id):
    result = document_manager.list_shares_for_doc(doc_id)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result), 200

@app.route("/documents/<doc_id>", methods=["DELETE"])
@require_auth
def delete_document(doc_id):
    user = get_current_user()
    result = document_manager.delete_document(user["username"], doc_id)

    if "error" in result:
        if result["error"] == "Document not found":
            return jsonify(result), 404
        return jsonify(result), 403

    return jsonify(result), 200

@app.route("/admin/dashboard")
@require_auth
@require_role("admin")
def admin_dashboard():
    return render_template("admin.html")

@app.after_request
def set_security_headers(response):
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; " # Avoid unsafe-inline in production
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # XSS Protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=()'
    )

    # HSTS (HTTP Strict Transport Security)
    response.headers['Strict-Transport-Security'] = (
        'max-age=31536000; includeSubDomains'
    )
    return response

# for development, generate self-signed certificate:
# openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
# Flask with TLS:
# if __name__ == '__main__':
#     app.run(ssl_context=('cert.pem', 'key.pem'),
#             host='0.0.0.0',
#             port=5000)

# Force HTTPS:
# @app.before_request
# def require_https():
#     if not request.is_secure and not app.debug:
#         url = request.url.replace("http://", "https://", 1)
#         return redirect(url, code=301)