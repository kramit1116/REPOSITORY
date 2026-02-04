from flask import Flask,render_template,request,redirect,url_for,flash,session
from models import db, User, Product, Category, Order, Cart, Transaction
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps
from datetime import datetime
from app import app
import csv
from uuid import uuid4

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
    categories = Category.query.all()
    category_names = [category.name for category in categories]
    category_sizes = [len(category.products) for category in categories]
    return render_template('admin.html',categories=categories, category_names=category_names, category_sizes=category_sizes)

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
    category = Category.query.get(category_id)
    if not category:
        flash("Category does not exist.")
        return redirect(url_for('admin'))
    return render_template('category/show.html',category=category)
    

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

@app.route('/product/add/<int:category_id>')
@admin_required
def add_product(category_id):
    category = Category.query.get(category_id)
    categories = Category.query.all()
    if not category:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('product/add.html',category=category, categories=categories,now=now)

@app.route('/product/add', methods=['POST'])
@admin_required
def add_product_post():
    name = request.form['name']
    price = request.form['price']
    category_id = request.form['category_id']
    quantity = request.form['quantity']
    man_date = request.form['man_date']

    category = Category.query.get(category_id)
    if not category:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    if not name or not price or not man_date or not quantity:
        flash('Please fill all the required fields.')
        return redirect(url_for('add_product', category_id=category.id))
    
    try:
        price = float(price)
        quantity = int(quantity)
        man_date =  datetime.strptime(man_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Please enter valid values for price and quantity.')
        return redirect(url_for('add_product', category_id=category.id))
    
    if price < 0 or quantity < 0:
        flash('Price and quantity must be non-negative.')
        return redirect(url_for('add_product', category_id=category.id))
    
    if man_date > datetime.now().date():
        flash('Manufacture date cannot be in the future.')
        return redirect(url_for('add_product', category_id=category.id))

    new_product = Product(name=name, price=price, category_id=category.id, quantity=quantity, man_date=man_date)
    db.session.add(new_product)
    db.session.commit()
    flash('Product added successfully.')
    return redirect(url_for('show_category', category_id=category.id))

@app.route('/product/<int:id>/edit')
@admin_required
def edit_product(id):
    product = Product.query.get(id)
    categories = Category.query.all()
    if not product:
        flash('Product does not exist.')
        return redirect(url_for('admin'))
    return render_template('product/edit.html',product=product, categories=categories)

@app.route('/product/<int:id>/edit', methods=['POST'])
@admin_required 
def edit_product_post(id):
    name = request.form['name']
    price = request.form['price']
    category_id = request.form['category_id']
    quantity = request.form['quantity']
    man_date = request.form['man_date']

    category = Category.query.get(category_id)
    if not category:
        flash('Category does not exist.')
        return redirect(url_for('admin'))
    if not name or not price or not man_date or not quantity:
        flash('Please fill all the required fields.')
        return redirect(url_for('add_product', category_id=category.id))
    
    try:
        price = float(price)
        quantity = int(quantity)
        man_date =  datetime.strptime(man_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Please enter valid values for price and quantity.')
        return redirect(url_for('add_product', category_id=category.id))
    
    if price < 0 or quantity < 0:
        flash('Price and quantity must be non-negative.')
        return redirect(url_for('add_product', category_id=category.id))
    
    if man_date > datetime.now().date():
        flash('Manufacture date cannot be in the future.')
        return redirect(url_for('add_product', category_id=category.id))

    product = Product.query.get(id)
    product.name = name
    product.price = price
    product.category_id = category.id
    product.quantity = quantity
    product.man_date =  man_date
    db.session.commit()
    flash('Product edited successfully.')
    return redirect(url_for('show_category', category_id=category.id))

@app.route('/product/<int:id>/delete')
@admin_required
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        flash('Product does not exist.')
        return redirect(url_for('admin'))
    return render_template('product/delete.html',product=product)

@app.route('/product/<int:id>/delete',methods=['POST'])
@admin_required
def delete_product_post(id):
    product = Product.query.get(id)
    if not product:
        flash('Product does not exist.')
        return redirect(url_for('admin'))   
    category_id = product.category.id
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('show_category', category_id=category_id))

#user routes 

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    categories = Category.query.all()
    parameter = request.args.get('parameter')
    query = request.args.get('query')

    parameters = {
        'cname': 'Category Name',
        'pname': 'Product Name',
        'price': 'Max Price'
    }
    
    if parameter and query:
        if parameter == 'cname':
            categories = Category.query.filter(Category.name.ilike(f'%{query}%')).all()
            return render_template('index.html', categories=categories,parameters=parameters,value=query)
        elif parameter == 'pname':
            return render_template('index.html', categories=categories,param=parameter, query=query,parameters=parameters,value=query)
        elif parameter == 'price':
            query = float(query)
            return render_template('index.html',categories=categories,param=parameter,query=query,parameters=parameters,value=query)
    return render_template('index.html',categories=categories,parameters=parameters)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@auth_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash('Product does not exist.')
        return redirect(url_for('index'))
    quantity = request.form.get('quantity')
    try:
        quantity = int(quantity)
    except ValueError:
        flash('Invalid quantity.')
        return redirect(url_for('index'))
    if quantity <= 0 or quantity > product.quantity:
        flash(f'Quantity must be between 1 and {product.quantity}.')
        return redirect(url_for('index'))
    cart = Cart.query.filter_by(user_id=session['user_id'], product_id=product.id).first()
    
    if cart:
        if quantity + cart.quantity > product.quantity:
            flash(f'Cannot add {quantity} items to cart. Only {product.quantity - cart.quantity} items left')
            return redirect(url_for('index'))
        cart.quantity += quantity
    else:
        cart = Cart(user_id=session['user_id'], product_id=product_id, quantity=quantity)
        db.session.add(cart)
    db.session.commit()

    flash('Product added to cart successfully.')
    return redirect(url_for('index'))

@app.route('/search')
@auth_required
def search():
    query = request.args.get('query')
    if not query:
        flash('Please enter a search query.')
        return redirect(url_for('index'))
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    return render_template('search_results.html', products=products, query=query)

@app.route('/cart')
@auth_required
def cart():
    carts = Cart.query.filter_by(user_id=session['user_id']).all()
    total = sum(cart.product.price * cart.quantity for cart in carts)
    return render_template('cart.html', carts=carts,total=total)

@app.route('/cart/<int:id>/delete', methods=['POST'])
@auth_required
def delete_cart(id):
    cart = Cart.query.get(id)
    if not cart:
        flash('Cart item does not exist.')
        return redirect(url_for('cart'))
    if not cart.user_id == session['user_id']:
        flash('You are not authorized to delete this item.')
        return redirect(url_for('cart'))
    db.session.delete(cart)
    db.session.commit()
    flash('Cart item deleted successfully.')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@auth_required
def checkout():
    carts = Cart.query.filter_by(user_id=session['user_id']).all()
    if not carts:
        flash('Your cart is empty.')
        return redirect(url_for('cart'))
    
    transaction = Transaction(user_id=session['user_id'], datetime=datetime.now())
    for cart in carts:
        order = Order(
            transaction=transaction,
            product_id=cart.product_id,
            quantity=cart.quantity,
            price=cart.product.price * cart.quantity
        )
        if cart.quantity > cart.product.quantity:
            flash(f'Not enough stock for {cart.product.name}. Available: {cart.product.quantity}, In Cart: {cart.quantity}')
            return redirect(url_for('delete_cart', id=cart.id))
        cart.product.quantity -= cart.quantity
        db.session.add(order)
        db.session.delete(cart)
    db.session.add(transaction)
    db.session.commit()

    flash('Order placed successfully.')
    return redirect(url_for('orders'))

@app.route('/orders')
@auth_required
def orders():
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
    return render_template('orders.html', transactions=transactions)

@app.route('/export_csv')
@auth_required
def export_csv():
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    filename = uuid4().hex + '.csv'
    url = 'static/csv/' + filename
    with open(url, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Transaction ID', 'DateTime','Product Name', 'Quantity', 'Price'
        ])  # Write header
        for transaction in transactions:
            for order in transaction.orders:
                writer.writerow([
                    transaction.id,
                    transaction.datetime,
                    order.product.name,
                    order.quantity,
                    order.price
                ])
    return redirect(url_for('static', filename='csv/' + filename))            