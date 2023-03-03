from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def loginDetails():
    with sqlite3.connect('database.db') as connection:
        cur = connection.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            itemQuantity = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'],))
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM cart WHERE userId = ?", (userId, ))
            itemQuantity = cur.fetchone()[0]
    connection.close()
    return (loggedIn, firstName, itemQuantity)

@app.route("/")
def root():
    loggedIn, firstName,  itemQuantity = getLoginDetails()
    with sqlite3.connect('database.db') as connection:
        cur =connection.cursor()
        cur.execute("SELECT productId, name, price, description, image, quantity FROM products")
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, name from categories')
        categoryData = cur.fetchall()
        itemData = parse(itemData)
        return render_template("home.html", itemData = itemData, loggedIn = loggedIn, firstName = firstName, itemQuantity=itemQuantity, categoryData = categoryData)

@app.route("/add")
def 