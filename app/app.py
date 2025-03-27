from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import psutil
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # Use environment variable for secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "signup"

# User model with role field
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), nullable=False, default='user')  # Added role field: 'admin' or 'user'

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Server-side validation
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = "Username already exists."
        elif User.query.filter_by(email=email).first():
            error = "Email already exists."
        else:
            # Set role to 'user' by default
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password=hashed_password, role='user')
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("index"))

    return render_template("signup.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)

@app.route("/index")
@login_required
def index():
    users = User.query.all() if current_user.is_admin() else []  # Pass users only if admin
    return render_template("index.html", users=users)

@app.route("/metrics")
@login_required
def get_metrics():
    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent
    })

@app.route("/users")
@login_required
def users():
    if not current_user.is_admin():
        return redirect(url_for("index"))  # Redirect non-admins to dashboard
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("signup"))

# Debug route to list all users (for development only)
@app.route("/debug/users")
@login_required
def debug_users():
    if not current_user.is_admin():
        return redirect(url_for("index"))
    users = User.query.all()
    return render_template("debug_users.html", users=users)

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create an admin user if none exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Use environment variable for admin password
            hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            admin_user = User(username='admin', email='admin@example.com', password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created: username=admin, password={admin_password}")
    app.run(debug=True, host='0.0.0.0', port=5000)
