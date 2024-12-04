from flask import Flask, request, render_template, jsonify
from flask_mail import Mail, Message
import os

app = Flask(__name__, template_folder='Templates')

# Configuring Flask-Mail
app.config.update(
    MAIL_SERVER='Smtp52.mailservice25.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='marcom@datalogicsindia.com',
    MAIL_PASSWORD='MarkovanilFo&3'
)

# Set a secret key for session management
app.secret_key = os.urandom(24)

mail = Mail(app)

# Define valid credentials
VALID_CREDENTIALS = [
    {"username": "user", "password": "user@123"},
    {"username": "admin", "password": "admin@123"}
]

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    for cred in VALID_CREDENTIALS:
        if username == cred['username'] and password == cred['password']:
            return jsonify({"success": True, "message": "Login successful"})

    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/send_email', methods=['POST'])
def send_email():
    sender = request.form['sender']
    recipients = request.form['recipients'].split(',')
    cc = request.form.get('cc')
    bcc = request.form.get('bcc')
    subject = request.form['subject']
    message_html = request.form.get('message')
    body_text = request.form.get('body_text')
    
    # Create a Message object
    msg = Message(subject=subject, sender=sender, recipients=recipients)
    
    # Add CC and BCC if provided
    if cc:
        msg.cc = cc.split(',')
    if bcc:
        msg.bcc = bcc.split(',')
    
    # Handle optional HTML and plain text bodies
    if message_html:
        msg.html = message_html
    if body_text:
        msg.body = body_text
    
    # Handle attachment
    attachment = request.files.get('attachment')
    if attachment:
        filename = attachment.filename
        content_type = attachment.content_type
        msg.attach(filename, content_type, attachment.read())

    # Send email
    mail.send(msg)
    
    return 'Email sent successfully!'

@app.route('/')
def index():
    return render_template('Index.html')

if __name__ == '__main__':
    app.run(debug=True)
