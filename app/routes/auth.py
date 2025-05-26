from flask import Blueprint, flash, render_template, request, redirect, url_for, session

bp = Blueprint('auth', __name__, url_prefix='/auth')

users = {}

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash("Username already exists. Log in", "error")
            redirect(url_for('auth.login'))
        users[username] = password
        return redirect(url_for('auth.register'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['user'] = username
            return redirect(url_for('image.upload_image'))
        flash("Invalid username or password", "error")
        return redirect(url_for('auth.login'))
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))