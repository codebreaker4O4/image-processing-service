from flask import Blueprint, flash, render_template, request, redirect, url_for, session

bp = Blueprint('auth', __name__, url_prefix='/auth')

# In production, use a proper database
users = {}

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash("Username and password are required", "error")
            return render_template('register.html')
        
        if username in users:
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('register.html')
        
        # Store user credentials (in production, use hashed passwords and a database)
        
        users[username] = password
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash("Username and password are required", "error")
            return render_template('login.html')
        
        if users.get(username) == password:
            session['user'] = username
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for('image.upload_image'))
        
        flash("Invalid username or password", "error")
        return render_template('login.html')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    username = session.get('user')
    session.clear()
    if username:
        flash(f"Goodbye, {username}!", "info")
    return redirect(url_for('auth.login'))