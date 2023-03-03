import sqlite3

connection =sqlite3.connect('database.db')

connection.execute('''CREATE TABLE users (
    userId INTERGER PRIMARY KEY,
    password TEXT,
    email TEXT,
    firstName TEXT,
    address1 TEXT,
    address2 TEXT,
    zipcode TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    phone TEXT
)''')

connection.execute('''CREATE TABLE products(
    productId INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    description TEXT,
    image TEXT,
    quantity INTEGER,
    categoryId INTEGER,
    FOREIGN KEY(categoryId) REFERENCES categories(categoryId)
)''')

connection.execute('''CREATE TABLE cart(
    userId INTEGER,
    productId INTEGER,
    FOREIGN KEY(userId) REFERENCES users(userId),
    FOREIGN KEY(productId) REFERENCES products(productId)
)''')

connection.execute('''CREATE TABLE categories(
    categoryId INTEGER PRIMARY KEY,
    name Text
)''')

connection.close()