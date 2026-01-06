from flask import Flask,render_template,request,redirect,url_for,flash,session
from models import db, User, Product, Category, Order, Cart, Transaction
from werkzeug.security import generate_password_hash,check_password_hash
from app import app

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
    else:
        flash('Please log in to access this page.')
        return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    if not username or not password:
        flash('Please enter both username and password.')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User does not exist.')
        return redirect(url_for('login'))
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password.')
        return redirect(url_for('login'))
    session['user_id'] = user.id
    flash('Logged in successfully.')
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')
    name = request.form.get('name')
    if not username or not password or not confirm_password:
        flash('Please fill out all required fields.')
        return redirect(url_for('register'))
    if password != confirm_password:
        flash('Password do not match.')
        return redirect(url_for('register'))
    user = User.query.filter_by(username=username).first()
    if user:
        flash('User already exists.')
        return redirect(url_for('register'))
    passhash = generate_password_hash(password)
    new_user = User(username=username, passhash=passhash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

