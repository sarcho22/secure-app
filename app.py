from flask import Flask, render_template
import config
import services

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

@app.route('/')
def index():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/login', methods=['POST'])
def login():
    # auth user

    # create session

    return response

@app.route('/admin/dashboard')
@services.authz.require_auth
@services.authz.require_role('admin')
def admin_dashboard():
    return render_template('admin.html')

# make sure password == confirmation for register



# @app.after_request
# def set_headers(response):
#     from services.security_headers import apply_security_headers
#     return apply_security_headers(response)


# keep route decorators, @app.before_request, @app.after_request
# routes should import from services:
# from services.user_manager import register_user
# from services.session_manager import SessionManager