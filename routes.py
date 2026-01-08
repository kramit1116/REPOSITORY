from flask import Flask,render_template,request,redirect,url_for,flash,session
from models import db, User, Product, Category, Order, Cart, Transaction
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps
from app import app

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

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue.')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page.')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    return render_template('index.html')

@app.route('/profile')
@auth_required
def profile():
    user = User.query.filter_by(id=session['user_id']).first()
    return render_template('profile.html', user=user)

# write route for editing profile
@app.route('/profile', methods=["POST"])
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form['password']
    name = request.form['name']

    if not username or not cpassword or not password:
        flash('Please fill all the required fields.')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])

    if not check_password_hash(user.passhash, cpassword):
        flash('Please enter the correct Password.')
        return redirect(url_for('profile'))
    
    if user.username != username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists.')
            return redirect(url_for('profile'))
        
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash('Profile updated successfully.')
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html',categories=Category.query.all())

@app.route('/category/add')
@admin_required
def add_category():
    return render_template('category/add.html')

@app.route('/category/add', methods=['POST'])
@admin_required
def add_category_post():
    name = request.form['name']
    if not name:
        flash('Category name is required.')
        return redirect(url_for('add_category'))
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
    flash('Category added successfully.')
    return redirect(url_for('admin'))

@app.route('/category/<int:category_id>')
@admin_required
def show_category(category_id):
    return f'Category {category_id}'

@app.route('/category/<int:category_id>/edit')
@admin_required
def edit_category(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    return render_template('category/edit.html',category=cat)

@app.route('/category/<int:category_id>/edit', methods=['POST'])
@admin_required
def edit_category_post(category_id):
    cat = Category.query.get(category_id)
    if not cat:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    name = request.form['name']
    if not name or Category.query.filter(Category.name==name, Category.id!=category_id).first():
        flash('Category name is required and must be unique.')
        return redirect(url_for('edit_category', category_id=category_id))
    cat.name = name
    db.session.commit()
    flash('Category updated successfully.')
    return redirect(url_for('admin'))

@app.route('/category/<int:category_id>/delete')
@admin_required
def delete_category(category_id):
    return render_template('category/delete.html',category=Category.query.get(category_id))

@app.route('/category/<int:category_id>/delete',methods= ['POST'])
@admin_required
def delete_category_post(category_id):
    category = Category.query.get(category_id)
    if not category:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully.')
    return redirect(url_for('admin'))
