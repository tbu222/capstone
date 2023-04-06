import os
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, flash, redirect, session, g, abort, url_for, current_app
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_uploads import IMAGES, UploadSet, configure_uploads, patch_request_class
from forms import UserAddForm, UserEditForm, LoginForm, ProductAddForm, CustomerRegisterForm, CustomerLoginForm
from models import db, connect_db, User, Brand, Category, Addproduct, Register, CustomerOrder
import secrets
from flask_msearch import Search
import stripe

publishable_key = 'pk_test_51Mu24DEWnuVoOV60khONQ6e9OJdzmn13ippXLRDHhIfbFB3uAgfP150YHsUhUSErujgw3AxZX0qt7wK8DH5Lr6wc00iVAzJZvK'

stripe.api_key = 'sk_test_51Mu24DEWnuVoOV60cTgYRZEh72I4XsrlBsJMnFbcwFgDkCE4rFwzPUygIFsEuXpPvV9OCqPuvly6Pgo5gx5TiqzD00a6j9djCh'

CURR_USER_KEY = "curr_user"

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///market'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "secret")
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'static/images')
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)   
toolbar = DebugToolbarExtension(app)
search = Search(db=db)
search.init_app(app)
bcrypt = Bcrypt()


connect_db(app)
db.create_all()

# def brands():
#     brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
#     return brands

# def categories():
#     categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
#     return categories
##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")

##############################################################################
# add brand and category

@app.route('/addbrand', methods=['GET','POST'])
def addbrand():
    if request.method=="POST":
        getbrand = request.form.get('brand')
        brand = Brand(name=getbrand)
        db.session.add(brand)
        flash(f'The Brand {getbrand} was added to your data', 'success')
        db.session.commit()
        return redirect("/addbrand")
    return render_template('products/addbrand.html', brands='brands')

@app.route('/updatebrand/<int:id>', methods=['GET','POST'])
def updatebrand(id):
    if g.user:
        updatebrand= Brand.query.get_or_404(id)
        brand = request.form.get('brand')
        if request.method == "POST":
            updatebrand.name = brand
            flash(f'Your brand  has been updated', 'success')
            db.session.commit()
            return redirect(url_for('brands'))
        return render_template('products/updatebrand.html', updatebrand=updatebrand)
    else:
        return render_template('home-anon.html')

@app.route('/deletebrand/<int:id>', methods=['POST'])
def deletebrand(id):
    brand = Brand.query.get_or_404(id)
    if request.method=="POST":
        db.session.delete(brand)
        db.session.commit()
        flash(f'The Brand {brand.name} has been deleted', 'success')
        return redirect(url_for('brands'))
    flash(f"The Brand {brand.name} can't be deleted", 'warning')
    return redirect(url_for('brands'))

@app.route('/brand/<int:id>')
def get_brand(id):
    get_b = Brand.query.filter_by(id=id).first_or_404()
    page = request.args.get('page', 1, type=int)
    brand= Addproduct.query.filter_by(brand=get_b).paginate(page=page, per_page=4)
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    return render_template('products/index.html', brand=brand, brands = brands, categories= categories, get_b=get_b)

@app.route('/addcat', methods=['GET','POST'])
def addcat():
    if request.method=="POST":
        getcat = request.form.get('category')
        cat = Category(name=getcat)
        db.session.add(cat)
        flash(f'The Category {getcat} was added to your data', 'success')
        db.session.commit()
        return redirect("/addcat")
    return render_template('products/addbrand.html')

@app.route('/updatecat/<int:id>', methods=['GET','POST'])
def updatecat(id):
    if g.user:
        updatecat= Category.query.get_or_404(id)
        category = request.form.get('category')
        if request.method == "POST":
            updatecat.name = category
            flash(f'Your category  has been updated', 'success')
            db.session.commit()
            return redirect(url_for('category'))
        return render_template('products/updatebrand.html', updatecat=updatecat)
    else:
        return render_template('home-anon.html')

@app.route('/deletecat/<int:id>', methods=['POST'])
def deletecat(id):
    category = Category.query.get_or_404(id)
    if request.method=="POST":
        db.session.delete(category)
        db.session.commit()
        flash(f'The Brand {category.name} has been deleted', 'success')
        return redirect(url_for('category'))
    flash(f"The Brand {category.name} can't be deleted", 'warning')
    return redirect(url_for('category'))

@app.route('/categories/<int:id>')
def get_category(id):
    page = request.args.get('page', 1, type=int)
    get_cat = Category.query.filter_by(id=id).first_or_404()
    get_cat_prod = Addproduct.query.filter_by(category=get_cat).paginate(page=page, per_page=4)
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    return render_template('products/index.html', get_cat_prod=get_cat_prod, categories = categories, brands= brands, get_cat=get_cat)
##############################################################################
# add product

@app.route('/addproduct', methods=['GET','POST'])
def addproduct():
    brands = Brand.query.all()
    categories = Category.query.all()
    form = ProductAddForm(request.form)
    if request.method == "POST":
        name = form.name.data
        price = form.price.data
        discount = form.discount.data
        stock =  form.stock.data
        description = form.description.data
        colors = form.colors.data
        brand = request.form.get('brand')
        category = request.form.get('category')
        image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
        image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
        image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
        addproduct = Addproduct(name=name, price=price,  discount=discount, stock=stock, colors=colors, desc=description,brand_id=brand, category_id=category, image_1=image_1, image_2=image_2, image_3= image_3)
        db.session.add(addproduct)
        flash(f'The product {name} has been added to your database','success')
        db.session.commit()
        return redirect("/")
    return render_template('products/addproduct.html', title="Add Product Page", form=form, brands=brands, categories=categories)

@app.route('/updateproduct/<int:id>', methods=['GET', 'POST'])
def updateproduct(id):
    if g.user:
        categories = Category.query.all()
        brands = Brand.query.all()
        product = Addproduct.query.get_or_404(id)
        brand = request.form.get('brand')
        category = request.form.get('category')
        form = ProductAddForm(request.form)
        if request.method == "POST":
            product.name = form.name.data
            product.price = form.price.data
            product.discount = form.discount.data
            product.brand_id = brand
            product.category_id = category
            product.colors = form.colors.data
            product.desc = form.description.data
            if request.files.get('image_1'):
                try:
                    os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
                    product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
                except:
                    product.image_1 = photos.save(request.files.get('image_1'), name=secrets.token_hex(10) + ".")
            if request.files.get('image_2'):
                try:
                    os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
                    product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
                except:
                    product.image_2 = photos.save(request.files.get('image_2'), name=secrets.token_hex(10) + ".")
            if request.files.get('image_3'):
                try:
                    os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
                    product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")
                except:
                    product.image_3 = photos.save(request.files.get('image_3'), name=secrets.token_hex(10) + ".")

            db.session.commit()
            flash(f'Product has been updated','success')
            return redirect(url_for('admin'))
        form.name.data= product.name
        form.price.data= product.price
        form.discount.data = product.discount
        form.stock.data = product.stock
        form.colors.data = product.colors
        form.description.data = product.desc

        return render_template('products/updateproduct.html', product=product, form=form, categories=categories, brands=brands )
    else:
        return render_template('home-anon.html')

@app.route('/deleteproduct/<int:id>', methods=['POST'])
def deleteproduct(id):
    product = Addproduct.query.get_or_404(id)
    if request.method == "POST":
        try:
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_1))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_2))
            os.unlink(os.path.join(current_app.root_path, "static/images/" + product.image_3))
        except Exception as e:
            print(e)
        
        db.session.delete(product)
        db.session.commit()
        flash(f'The product {product.name} has been deleted', 'success')
        return redirect(url_for('admin'))
    flash(f"Can't delete the product, 'danger")
    return redirect(url_for('admin'))

@app.route('/product/<int:id>')
def single_page(id):
    product = Addproduct.query.get_or_404(id)
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    return render_template('products/single_page.html', product=product, brands=brands, categories=categories)
##############################################################################
#add brand admin
@app.route('/brands')
def brands():
    if g.user:
        brands = Brand.query.order_by(Brand.id.desc()).all()
        return render_template('admin/brand.html', brands=brands)

    else:
        return render_template('home-anon.html')

@app.route('/category')
def category():
    if g.user:
        categories = Category.query.order_by(Category.id.desc()).all()
        return render_template('admin/brand.html', categories=categories)

    else:
        return render_template('home-anon.html')

##############################################################################
# Cart
def MergeDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False

@app.route('/addcart', methods=['POST'])
def AddCart():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        colors=request.form.get('colors')
        product= Addproduct.query.filter_by(id=product_id).first()
        if product_id and quantity and colors and request.method == "POST":
            DictItems = {product_id:{'name': product.name, 'price':float(product.price), 'discount': product.discount, 'color': colors, 'quantity': quantity, 'image': product.image_1, 'colors':product.colors}}         
            if "Shoppingcart" in session:
                if product_id in session['Shoppingcart']:
                    for key,item in session['Shoppingcart'].items():
                        if int(key) == int(product_id):
                            session.modified = True
                            item['quantity'] +=1
                else:
                    session["Shoppingcart"] = MergeDicts(session["Shoppingcart"], DictItems)
                    return redirect(request.referrer)
            else:
                session["Shoppingcart"] = DictItems
                return redirect(request.referrer)
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

@app.route('/carts')
def getCart():
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <=0:
        return redirect(url_for('homepage'))
    subtotal = 0
    grandtotal = 0
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    for key, product in session['Shoppingcart'].items():
        discount=(product['discount']/100 * float(product['price']) *int(product['quantity'])) 
        subtotal += float(product['price']) * int(product['quantity'])
        subtotal -= discount
        tax = ("%.2f" % (.06 * float(subtotal)))
        grandtotal = float("%.2f"% (1.06 * subtotal))
    return render_template('products/carts.html', tax = tax, grandtotal = grandtotal, brands=brands, categories=categories)

@app.route('/empty')
def empty_cart():
    try:
        session.clear()
        return redirect(url_for('homepage'))
    except Exception as e:
        print(e)

@app.route('/clearcart')
def clearcart():
    try:
        session.pop('Shoppingcart', None)
        return redirect(url_for('homepage'))
    except Exception as e:
        print(e)
@app.route('/updatecart/<int:code>', methods=['POST'])
def updatecart(code):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:    
        return redirect(url_for('homepage'))
    if request.method == "POST":
        quantity = request.form.get('quantity')
        color = request.form.get('color')
        try:
            session.modified = True
            for key, item in session['Shoppingcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    item['color'] = color
                    flash('Item is updated!')
                    return redirect(url_for('getCart'))
        except Exception as e:
            print(e)
            return redirect(url_for('getCart'))

@app.route('/deleteitem/<int:id>')
def deleteitem(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('homepage'))
    try:
        session.modified = True
        for key, item in session['Shoppingcart'].items():
            if int(key) == id:
                print(key)
                session['Shoppingcart'].pop(key, None)
                print(session['Shoppingcart'])
                return redirect(url_for('getCart'))
    except Exception as e:
        print(e)
        return redirect(url_for('getCart'))
##############################################################################
# Homepage and error pages


@app.route('/admin')
def adminpage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        products = Addproduct.query.all()
        return render_template('home.html', products=products)

    else:
        return render_template('home-anon.html')

@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    page = request.args.get('page', 1, type=int)
    products = Addproduct.query.filter(Addproduct.stock > 0).order_by(Addproduct.id.desc()).paginate(page=page, per_page=4)
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    return render_template('products/index.html', products = products, brands = brands, categories =categories)

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404
##############################################################################
#search
@app.route('/result')
def result():
    searchword = request.args.get('q')
    products = Addproduct.query.msearch(searchword, fields=['name', 'desc'], limit=6)
    brands = Brand.query.join(Addproduct,(Brand.id == Addproduct.brand_id)).all()
    categories = Category.query.join(Addproduct, (Category.id == Addproduct.category_id)).all()
    return render_template('products/result.html', products=products, brands = brands, categories =categories)


##############################################################################
#customer register
# @app.route('/customer/register', methods=['GET', 'POST'])
# def customer_register():
#     form = CustomerRegisterForm()
#     if form.validate_on_submit():
#         hash_password = bcrypt.generate_password_hash(form.password.data)
#         register = Register(name=form.name.data, username= form.username.data, email=form.email.data, password = hash_password, country= form.country.data, state= form.state.data, city=form.city.data, address=form.address.data,zipcode=form.zipcode.data)
#         db.session.add(register)
#         flash('Welcome {form.name.data} to Market', 'success')
#         db.session.commit()
#         return redirect("/login")
#     return render_template('customers/register.html', form=form)

# @app.route('/customer/login', methods=['GET', 'POST'])
# def customerLogin():
#     form = CustomerLoginForm()
#     if form.validate_on_submit():
#         user = Register.query.filter_by(email=form.email.data).first()
#         if user and bcrypt.check_password_hash(user.password, form.password.data):
#             login_user(user)
#             flash('You are login now', 'success')
#             next = request.args.get('next')
#             return redirect(next or url_for('homepage'))
#         flash('incorrect email or password')
#         return redirect(url_for('customerLogin'))
#     return render_template('customers/login.html', form=form)
##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.route('/getorder')
def get_order():
    if g.user:
        customer_id = g.user.id
        invoice = secrets.token_hex(5)
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id, orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been updated','success')
            return redirect(url_for('orders',invoice = invoice))
        except Exception as e:
            print(e)
            flash('404', 'danger')
            return redirect(url_for('getCart'))

    else:
        return render_template('home-anon.html')
@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req

@app.route('/orders/<invoice>')
def orders(invoice):
    if g.user:
        grandTotal = 0
        subTotal = 0
        customer_id = g.user.id
        customer = User.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount']/100 * float(product['price']) *int(product['quantity'])) 
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = ("%.2f"% (1.06 * float(subTotal)))
    else:
        return render_template('home-anon.html')
    return render_template('customers/order.html', invoice=invoice, tax= tax, subTotal = subTotal, grandTotal=grandTotal, customer=customer, orders=orders)

@app.route('/payment', methods=['POST'])
def payment():
    invoice = request.form.get('invoice')
    amount = request.form.get('amount')
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        description='Market',
        amount=amount,
        currency='usd',
    )
    orders = CustomerOrder.query.filter_by(customer_id=g.user.id).order_by(CustomerOrder.id.desc()).first()
    orders.status = 'Paid'
    db.session.commit()
    return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    return render_template('customers/thanks.html')
