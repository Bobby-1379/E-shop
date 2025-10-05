from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- DATABASE MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product.html', product=product)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='sha256')
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials!", "danger")
            return redirect(url_for('login'))
        session['user_id'] = user.id
        session['username'] = user.username
        flash("Logged in successfully!", "success")
        return redirect(url_for('index'))
    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('index'))

# ---------------- ADD TO CART ----------------
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        
        return redirect(url_for('login'))
    user_id = session['user_id']
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash("Product added to cart!", "success")
    return redirect(url_for('index'))

# ---------------- CART PAGE ----------------
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))
    user_id = session['user_id']
    items = CartItem.query.filter_by(user_id=user_id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=total)

# ---------------- UPDATE CART ----------------
@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = int(request.form['quantity'])
    cart_item = CartItem.query.get_or_404(item_id)
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    db.session.commit()
    return redirect(url_for('cart'))

# ---------------- CHECKOUT ----------------
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))
    user_id = session['user_id']
    items = CartItem.query.filter_by(user_id=user_id).all()
    total = sum(item.product.price * item.quantity for item in items)
    for item in items:
        db.session.delete(item)
    db.session.commit()
    flash(f"Checkout successful! Total paid: ${total:.2f}", "success")
    return render_template('checkout.html')

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Add sample products if none exist
        if Product.query.count() == 0:
            sample_products = [
                Product(name="Washing Machine", description="Front Load Fully Automatic", price=399, image="washing.jpg"),
                Product(name="Smartphone", description="Latest model smartphone", price=699, image="smartphone.jpg"),
                Product(name="Laptop", description="Powerful gaming laptop", price=1200, image="laptop.jpg"),
                Product(name="Headphones", description="Noise-cancelling headphones", price=199, image="headphone.jpg")
            ]
            db.session.bulk_save_objects(sample_products)
            db.session.commit()
    app.run(debug=True)
