from flask import Flask, redirect, request, jsonify, make_response, render_template, send_file
import config, io, os
from services.storage import save_json
from services.user_manager import register_user, authenticate_user, get_all_users, promote_user
from services.security_logger import SecurityLogger
from services.session_manager import SessionManager
from services.document_manager import DocumentManager
from services.authz import require_auth, require_any_role, get_current_user

app = Flask(__name__)

app.config["SECRET_KEY"] = config.SECRET_KEY

session_manager = SessionManager()
document_manager = DocumentManager()
security_logger = SecurityLogger()

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

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
@require_auth(security_logger)
def dashboard():
    return render_template("dashboard.html")

@app.route("/documents-page")
@require_auth(security_logger)
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
        # not sure if i need to log this
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=username,
            details="Passwords do not match",
            severity="ERROR"
        )
        return jsonify({"error": "Passwords do not match"}), 400

    result = register_user(username, email, password)

    if "error" in result:
        # registration failed (dup username/email)
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=username,
            details=result["error"],
            severity="ERROR"
        )
        return jsonify(result), 400
    
    # registration success
    security_logger.log_event(
        event_type="REGISTER_SUCCESS",
        user_id=username,
        details="User registered successfully with guest role"
    )

    return jsonify(result), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form

    username = data.get("username", "").strip()
    password = data.get("password", "")

    # log attempt
    security_logger.log_event(
        event_type="LOGIN_ATTEMPT",
        user_id=username,
        details="User attempted login"
    )

    result = authenticate_user(username, password)
    if "error" in result:
        if result["error"] == "Account is temporarily locked":
            security_logger.log_event(
                event_type="AUTHENTICATION_FAILURE",
                user_id=username,
                details="Reached maximum login attempts. Account locked.",
                severity="CRITICAL"
            )
        else:
        # authentication failure
            security_logger.log_event(
                event_type="AUTHENTICATION_FAILURE",
                user_id=username,
                details=result["error"],
                severity="WARNING"
            )
        return jsonify(result), 401

    user = result["user"]
    # authentication success
    security_logger.log_event(
        event_type="AUTHENTICATION_SUCCESS",
        user_id=user["username"],
        details="User authenticated successfully"
    )

    token = session_manager.create_session(user["username"])
    # session creation
    security_logger.log_event(
        event_type="SESSION_CREATED",
        user_id=user["username"],
        details="Session token issued"
    )

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
@require_auth(security_logger)
def logout():
    token = request.cookies.get("session_token")
    if token:
        session_manager.destroy_session(token)

    security_logger.log_event(
        event_type="SESSION_DESTROYED",
        user_id=request.user["username"],
        details="User logged out and session destroyed"
    )

    response = make_response(jsonify({
        "success": True,
        "message": "Logged out"
    }))
    response.delete_cookie("session_token")
    return response


@app.route("/me", methods=["GET"])
@require_auth(security_logger)
def me():
    return jsonify({
        "username": request.user["username"],
        "email": request.user["email"],
        "role": request.user["role"]
    })

@app.route("/upload", methods=["POST"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def upload():
    if "file" not in request.files:
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details="Upload failed: no file provided",
            severity="ERROR"
        )
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details="Upload failed: no file selected",
            severity="ERROR"
        )
        return jsonify({"error": "No file selected"}), 400

    result = document_manager.upload_file(
        request.user["username"],
        file
    )

    if "error" in result:
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details=f"Upload failed: {result['error']}",
            severity="ERROR"
        )
        return jsonify(result), 400

    security_logger.log_event(
        event_type="DATA_CREATE",
        user_id=request.user["username"],
        details=f"Uploaded document: {file.filename}"
    )

    return jsonify(result), 201


@app.route("/documents", methods=["GET"])
@require_auth(security_logger)
def list_documents():
    documents = document_manager.get_user_documents(request.user["username"])

    security_logger.log_event(
        event_type="DATA_READ",
        user_id=request.user["username"],
        details="User viewed document list"
    )

    return jsonify({"documents": documents})

@app.route("/download/<doc_id>", methods=["GET"])
@require_auth(security_logger)
def download(doc_id):
    result = document_manager.get_file(request.user["username"], doc_id)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_READ",
                user_id=request.user["username"],
                details=f"Download failed: document {doc_id} not found",
                severity="ERROR"
            )
            return jsonify(result), 404
        security_logger.log_event(
            event_type="AUTHORIZATION_FAILURE",
            user_id=request.user["username"],
            details=f"Unauthorized download attempt for document {doc_id}",
            severity="WARNING"
        )
        return jsonify(result), 403

    file_bytes = result["data"]
    filename = result["filename"]

    security_logger.log_event(
        event_type="DATA_READ",
        user_id=request.user["username"],
        details=f"Downloaded document: {filename}"
    )

    return send_file(
        io.BytesIO(file_bytes),
        as_attachment=True,
        download_name=filename
    )

@app.route("/replace", methods=["POST"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def replace_document():
    if "file" not in request.files:
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details="Replace failed: no file provided",
            severity="ERROR"
        )
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details="Replace failed: no file selected",
            severity="ERROR"
        )
        return jsonify({"error": "No file selected"}), 400

    doc_id = request.form.get("doc_id", "").strip()

    result = document_manager.replace_file(request.user["username"], doc_id, file)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_UPDATE",
                user_id=request.user["username"],
                details=f"Replace failed: document {doc_id} not found",
                severity="ERROR"
            )
            return jsonify(result), 404
        security_logger.log_event(
            event_type="AUTHORIZATION_FAILURE",
            user_id=request.user["username"],
            details=f"Unauthorized replace attempt for document {doc_id}",
            severity="WARNING"
        )
        return jsonify(result), 403
    
    security_logger.log_event(
        event_type="DATA_UPDATE",
        user_id=request.user["username"],
        details=f"Replaced document {doc_id} with file {file.filename}"
    )
    return jsonify(result), 200

@app.route("/share", methods=["POST"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def share_document():
    data = request.get_json(silent=True) or request.form

    doc_id = data.get("doc_id", "").strip()
    target_username = data.get("target_username", "").strip()
    role = data.get("role", "").strip()

    result = document_manager.share_document(request.user["username"], doc_id, target_username, role)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_UPDATE",
                user_id=request.user["username"],
                details=f"Share failed: document {doc_id} not found",
                severity="ERROR"
            )
            return jsonify(result), 404
        if result["error"] == "Forbidden":
            security_logger.log_event(
                event_type="AUTHORIZATION_FAILURE",
                user_id=request.user["username"],
                details=f"Unauthorized share attempt for document {doc_id}",
                severity="WARNING"
            )
            return jsonify(result), 403
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details=f"Share failed: {result['error']}",
            severity="ERROR"
        )
        return jsonify(result), 400

    security_logger.log_event(
        event_type="DATA_UPDATE",
        user_id=request.user["username"],
        details=f"Shared document {doc_id} with {target_username} as {role}"
    )
    return jsonify(result), 200


@app.route("/unshare", methods=["POST"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def unshare_document():
    data = request.get_json(silent=True) or request.form

    doc_id = data.get("doc_id", "").strip()
    target_username = data.get("target_username", "").strip()

    result = document_manager.unshare_document(request.user["username"], doc_id, target_username)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_UPDATE",
                user_id=request.user["username"],
                details=f"Unshare failed: document {doc_id} not found",
                severity="ERROR"
            )
            return jsonify(result), 404
        if result["error"] == "Forbidden":
            security_logger.log_event(
                event_type="AUTHORIZATION_FAILURE",
                user_id=request.user["username"],
                details=f"Unauthorized unshare attempt for document {doc_id}",
                severity="WARNING"
            )
            return jsonify(result), 403
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details=f"Unshare failed: {result['error']}",
            severity="ERROR"
        )
        return jsonify(result), 400
    
    security_logger.log_event(
        event_type="DATA_UPDATE",
        user_id=request.user["username"],
        details=f"Unshared document {doc_id} from {target_username}"
    )
    return jsonify(result), 200


@app.route("/shares/<doc_id>", methods=["GET"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def list_shares(doc_id):
    result = document_manager.list_shares_for_doc(request.user["username"], doc_id)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_READ",
                user_id=request.user["username"],
                details=f"List shares failed: document {doc_id} not found",
                severity="WARNING"
            )
            return jsonify(result), 404

        security_logger.log_event(
            event_type="AUTHORIZATION_FAILURE",
            user_id=request.user["username"],
            details=f"Unauthorized share list access for document {doc_id}",
            severity="WARNING"
        )
        return jsonify(result), 403

    security_logger.log_event(
        event_type="DATA_READ",
        user_id=request.user["username"],
        details=f"Viewed share list for document {doc_id}"
    )
    return jsonify(result), 200

@app.route("/documents/<doc_id>", methods=["DELETE"])
@require_auth(security_logger)
@require_any_role(security_logger, "user", "admin")
def delete_document(doc_id):
    result = document_manager.delete_document(request.user["username"], doc_id)

    if "error" in result:
        if result["error"] == "Document not found":
            security_logger.log_event(
                event_type="DATA_DELETE",
                user_id=request.user["username"],
                details=f"Delete failed: document {doc_id} not found",
                severity="ERROR"
            )
            return jsonify(result), 404
        security_logger.log_event(
            event_type="AUTHORIZATION_FAILURE",
            user_id=request.user["username"],
            details=f"Unauthorized delete attempt for document {doc_id}",
            severity="WARNING"
        )
        return jsonify(result), 403

    security_logger.log_event(
        event_type="DATA_DELETE",
        user_id=request.user["username"],
        details=f"Deleted document {doc_id}"
    )
    return jsonify(result), 200

@app.route("/admin/dashboard")
@require_auth(security_logger)
@require_any_role(security_logger, "admin")
def admin_dashboard():
    security_logger.log_event(
        event_type="DATA_READ",
        user_id=request.user["username"],
        details="Accessed admin dashboard"
    )
    return render_template("admin.html")

@app.route("/admin/users", methods=["GET"])
@require_auth(security_logger)
@require_any_role(security_logger, "admin")
def admin_list_users():
    users = get_all_users()

    security_logger.log_event(
        event_type="DATA_READ",
        user_id=request.user["username"],
        details="Admin viewed all users"
    )

    safe_users = []
    for user in users:
        safe_users.append({
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        })

    return jsonify({"users": safe_users}), 200

@app.route("/admin/promote", methods=["POST"])
@require_auth(security_logger)
@require_any_role(security_logger, "admin")
def admin_promote_user():
    data = request.get_json(silent=True) or request.form
    target_username = data.get("target_username", "").strip()

    if not target_username:
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details="Admin promotion failed: missing target username",
            severity="WARNING"
        )
        return jsonify({"error": "Target username required"}), 400

    result = promote_user(target_username)

    if "error" in result:
        security_logger.log_event(
            event_type="INPUT_VALIDATION_FAILURE",
            user_id=request.user["username"],
            details=f"Admin promotion failed for {target_username}: {result['error']}",
            severity="WARNING"
        )
        return jsonify(result), 400

    security_logger.log_event(
        event_type="SECURITY_CONFIGURATION_CHANGE",
        user_id=request.user["username"],
        details=f"Promoted {target_username} from guest to user"
    )

    return jsonify(result), 200

# Force HTTPS:
@app.before_request
def require_https():
    if not request.is_secure and not app.debug:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

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
if __name__ == '__main__':
    app.run(ssl_context=('cert.pem', 'key.pem'),
            host='0.0.0.0',
            port=5000)

