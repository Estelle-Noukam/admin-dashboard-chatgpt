from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.String(100), nullable=False)

# =========================
# DATABASE INIT
# =========================

with app.app_context():

    db.create_all()

    admin_exists = User.query.filter_by(username='admin').first()

    if not admin_exists:

        admin = User(
            username='admin',
            password=generate_password_hash('admin'),
            role='admin'
        )

        db.session.add(admin)

        sample_data = [
            Data(
                title='Rapport 1',
                content='Contenu du rapport 1',
                created_at=str(datetime.now())
            ),
            Data(
                title='Rapport 2',
                content='Contenu du rapport 2',
                created_at=str(datetime.now())
            )
        ]

        db.session.add_all(sample_data)

        db.session.commit()

# =========================
# HELPERS
# =========================

def current_user():

    if 'user_id' in session:
        return User.query.get(session['user_id'])

    return None

def is_admin():

    user = current_user()

    return user and user.role == 'admin'

# =========================
# HOME
# =========================

@app.route('/')
def index():

    return render_template(
        'index.html',
        user=current_user()
    )

# =========================
# AUTH
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:

            flash('Utilisateur déjà existant')

            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            role='user'
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template(
        'register.html',
        user=current_user()
    )

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id

            return redirect(url_for('dashboard'))

        flash('Identifiants invalides')

    return render_template(
        'login.html',
        user=current_user()
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('index'))

# =========================
# PROFILE
# =========================

@app.route('/profile')
def profile():

    user = current_user()

    if not user:
        return redirect(url_for('login'))

    return render_template(
        'profile.html',
        user=user
    )

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    user = current_user()

    if not user:
        return redirect(url_for('login'))

    total_users = User.query.count()
    total_data = Data.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    normal_users = User.query.filter_by(role='user').count()

    latest_data = Data.query.order_by(Data.id.desc()).all()

    return render_template(
        'dashboard.html',
        total_users=total_users,
        total_data=total_data,
        admin_users=admin_users,
        normal_users=normal_users,
        latest_data=latest_data,
        user=user
    )

# =========================
# REPORTS
# =========================

@app.route('/reports')
def reports():

    user = current_user()

    if not user:
        return redirect(url_for('login'))

    total_users = User.query.count()
    total_data = Data.query.count()

    return render_template(
        'reports.html',
        total_users=total_users,
        total_data=total_data,
        user=user
    )

# =========================
# ADMIN USERS
# =========================

@app.route('/admin/users')
def admin_users():

    if not is_admin():
        return redirect(url_for('dashboard'))

    users = User.query.all()

    return render_template(
        'admin_users.html',
        users=users,
        user=current_user()
    )

@app.route('/admin/users/delete/<int:id>')
def delete_user(id):

    if not is_admin():
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin_users'))

# =========================
# DATA MANAGEMENT
# =========================

@app.route('/admin/data')
def admin_data():

    if not is_admin():
        return redirect(url_for('dashboard'))

    data_list = Data.query.all()

    return render_template(
        'admin_data.html',
        data_list=data_list,
        user=current_user()
    )

@app.route('/admin/data/create', methods=['GET', 'POST'])
def create_data():

    if not is_admin():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        data = Data(
            title=request.form['title'],
            content=request.form['content'],
            created_at=str(datetime.now())
        )

        db.session.add(data)
        db.session.commit()

        return redirect(url_for('admin_data'))

    return render_template(
        'create_data.html',
        user=current_user()
    )

@app.route('/admin/data/edit/<int:id>', methods=['GET', 'POST'])
def edit_data(id):

    if not is_admin():
        return redirect(url_for('dashboard'))

    data = Data.query.get_or_404(id)

    if request.method == 'POST':

        data.title = request.form['title']
        data.content = request.form['content']

        db.session.commit()

        return redirect(url_for('admin_data'))

    return render_template(
        'edit_data.html',
        data=data,
        user=current_user()
    )

@app.route('/admin/data/delete/<int:id>')
def delete_data(id):

    if not is_admin():
        return redirect(url_for('dashboard'))

    data = Data.query.get_or_404(id)

    db.session.delete(data)
    db.session.commit()

    return redirect(url_for('admin_data'))

# =========================
# RUN
# =========================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
