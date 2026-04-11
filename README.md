# secure-app

users, sessions, and docs are cleared before submission so grader can manually test project without preexisting data

1. Install dependencies using the following bash command: `pip install -r requirements.txt`

2. Set environment variables. Blank .env file will be provided.

3. Run the application - Start the app with HTTPS enabled with the following bash command: `python app.py` 

4. Access the app - Open the link in the terminal using your browser (you may need to accept a self-signed certificate warning). Will likely be something like `127.0.0.1:5000`

5. Basic usage flow
- register a new account
- log in
- access dashboard
- upload/manage documents

Troubleshooting
- if port 5000 is in use, change it in app.py
- if HTTPS fails, ensure cert.pem and key.pem exist
- if login issues occur, clear sessions.js