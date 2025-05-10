from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///worklogger.db'
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    total_earned = db.Column(db.Float, default=0.0)

class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin' if user.is_admin else 'work'))
        flash('Неверный логин или пароль!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Пользователь уже существует!')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна!')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/work', methods=['GET', 'POST'])
@login_required
def work():
    user = User.query.get(session['user_id'])
    active_session = WorkSession.query.filter_by(user_id=user.id, end_time=None).first()

    if request.method == 'POST':
        if 'start' in request.form and not active_session:
            new_session = WorkSession(user_id=user.id)
            db.session.add(new_session)
            db.session.commit()
            flash('Работа начата!')
        elif 'end' in request.form and active_session:
            active_session.end_time = datetime.utcnow()
            hours = (active_session.end_time - active_session.start_time).total_seconds() / 3600
            salary = hours * user.hourly_rate
            user.total_earned += salary
            db.session.commit()
            flash(f'Заработано: {salary:.2f} руб.')
        return redirect(url_for('work'))

    return render_template('work.html', user=user, active_session=active_session)

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('work'))

    employees = User.query.filter_by(is_admin=False).all()
    return render_template('admin.html', employees=employees)

@app.route('/admin/add_employee', methods=['POST'])
@login_required
def add_employee():
    if not session.get('is_admin'):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('work'))

    username = request.form['username']
    password = request.form['password']
    hourly_rate = float(request.form['hourly_rate'])

    if User.query.filter_by(username=username).first():
        flash('Пользователь уже существует!', 'error')
    else:
        new_employee = User(
            username=username,
            password=password,
            hourly_rate=hourly_rate
        )
        db.session.add(new_employee)
        db.session.commit()
        flash('Сотрудник добавлен!', 'success')

    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('work'))

    employee = User.query.get(employee_id)
    if not employee:
        flash('Сотрудник не найден!', 'error')
    elif employee.is_admin:
        flash('Нельзя удалить администратора!', 'error')
    else:
        WorkSession.query.filter_by(user_id=employee_id).delete()
        db.session.delete(employee)
        db.session.commit()
        flash('Сотрудник удален!', 'success')

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)