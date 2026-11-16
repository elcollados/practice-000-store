from flask import Flask, render_template, session, redirect, request
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
import sqlite3
import os
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv()

app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Set it in your .env file locally or in Render's Environment settings."
    )
if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "ADMIN_USERNAME / ADMIN_PASSWORD_HASH environment variables are not set. "
        "Admin login cannot work without them."
    )

app.secret_key = SECRET_KEY


DEBUG_MODE = os.getenv("FLASK_DEBUG", "0") == "1"


csrf = CSRFProtect(app)


def get_db():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=DictCursor)
        return conn

    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(cursor, query, values):

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        query = query.replace("?", "%s")

    cursor.execute(query, values)


def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        id_column = "id SERIAL PRIMARY KEY"
    else:
        id_column = "id INTEGER PRIMARY KEY AUTOINCREMENT"

    execute_query(
        cursor,
        f"""
    CREATE TABLE IF NOT EXISTS products (
        {id_column},
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT NOT NULL
    )
    """,
        ()
    )

    execute_query(
        cursor,
        f"""
    CREATE TABLE IF NOT EXISTS orders (
        {id_column},
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    """,
        ()
    )

    execute_query(
        cursor,
        f"""
    CREATE TABLE IF NOT EXISTS order_items (
        {id_column},
        order_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL
    )
    """,
        ()
    )

    execute_query(cursor, "SELECT COUNT(*) AS count  FROM products", ())
    count = cursor.fetchone()["count"]

    if count == 0:
        default_products = [
            ("Product 1", 500, "product1.jpg"),
            ("Product 2", 750, "product2.jpg"),
            ("Product 3", 1000, "product3.jpg"),
        ]

        for name, price, image in default_products:
            execute_query(
                cursor,
                "INSERT INTO products (name, price, image) VALUES (?, ?, ?)",
                (name, price, image)
            )

    conn.commit()
    conn.close()


def get_products():
    conn = get_db()
    cursor = conn.cursor()

    execute_query(cursor, "SELECT * FROM products ORDER BY id", ())
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return products


def get_product_by_id(product_id):
    conn = get_db()
    cursor = conn.cursor()

    execute_query(cursor, "SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    return product


@app.route("/")
def home():
    products = get_products()
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = get_product_by_id(product_id)

    if product is None:
        return "Product not found", 404

    return render_template("product_detail.html", product=product)


@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    cart_products = []

    for product_id_str, quantity in cart.items():

        product = get_product_by_id(int(product_id_str))

        if product:
            subtotal = product["price"] * quantity

            cart_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })

    total = 0

    for product in cart_products:
        total += product["subtotal"]

    return render_template(
        "cart.html",
        cart_products=cart_products,
        total=total
    )


@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    product = get_product_by_id(product_id)

    if product is None:
        return "Product not found", 404

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    quantity = int(request.form.get("quantity", 1))

    if quantity < 1 or quantity > 99:
        return "Invalid quantity", 400

    key = str(product_id)

    if key in cart:
        cart[key] += quantity
    else:
        cart[key] = quantity

    session["cart"] = cart

    return redirect("/cart")


@app.route("/remove-from-cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):

    cart = session.get("cart", {})
    key = str(product_id)

    if key in cart:
        del cart[key]
        session["cart"] = cart

    return redirect("/cart")


@app.route("/decrease-quantity/<int:product_id>", methods=["POST"])
def decrease_quantity(product_id):

    cart = session.get("cart", {})
    key = str(product_id)

    if key in cart:

        cart[key] -= 1

        if cart[key] <= 0:
            del cart[key]

    session["cart"] = cart

    return redirect("/cart")


@app.route("/increase-quantity/<int:product_id>", methods=["POST"])
def increase_quantity(product_id):

    cart = session.get("cart", {})
    key = str(product_id)

    if key in cart:
        cart[key] += 1

    session["cart"] = cart

    return redirect("/cart")


@app.route("/clear-cart", methods=["POST"])
def clear_cart():
    session.pop("cart", None)
    return redirect("/")


@app.route("/checkout")
def checkout():

    cart = session.get("cart", {})

    if not cart:
        return redirect("/cart")

    return render_template("checkout.html")


@app.route("/place-order", methods=["POST"])
def place_order():

    name = request.form["name"].strip()
    address = request.form["address"].strip()
    phone = request.form["phone"].strip()

    if not name or not address or not phone:
        return "Please fill in all fields."

    if not phone.isdigit():
        return "Phone number must contain digits only."

    cart = session.get("cart", {})

    if not cart:
        return redirect("/cart")

    cart_products = []

    for product_id_str, quantity in cart.items():

        product = get_product_by_id(int(product_id_str))

        if product:
            subtotal = product["price"] * quantity

            cart_products.append({
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })

    if not cart_products:
        return redirect("/cart")

    total = 0

    for product in cart_products:
        total += product["subtotal"]

    conn = get_db()
    cursor = conn.cursor()
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        
        execute_query(
            cursor,
            """
            INSERT INTO orders (name, address, phone, total)
            VALUES(?, ?, ?, ?)
            RETURNING id
            """,
            (name, address, phone, total)
        )
        order_id = cursor.fetchone()["id"]
    else:
        
        execute_query(
            cursor,
            """
            INSERT INTO orders (name, address, phone, total)
            VALUES(?, ?, ?, ?)
            """,
            (name, address, phone, total)
        )
        order_id = cursor.lastrowid

    for product in cart_products:

        execute_query(
            cursor,
            """
            INSERT INTO order_items
            (order_id, product_name, price, quantity, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                product["name"],
                product["price"],
                product["quantity"],
                product["subtotal"]
            )
        )

    conn.commit()
    conn.close()

    session.pop("cart", None)

    return render_template(
        "order.html",
        order_id=order_id,
        name=name,
        address=address,
        phone=phone,
        cart_products=cart_products,
        total=total
    )


@app.route("/track-order", methods=["GET", "POST"])
def track_order():

    order = None
    order_items = []

    if request.method == "POST":
        order_id = request.form["order_id"]
        phone = request.form.get("phone", "").strip()

        conn = get_db()
        cursor = conn.cursor()

        
        execute_query(
            cursor,
            "SELECT * FROM orders WHERE id = ? AND phone = ?",
            (order_id, phone)
        )
        order = cursor.fetchone()

        if order:
            execute_query(
                cursor,
                "SELECT * FROM order_items WHERE order_id = ?",
                (order_id,)
            )

            order_items = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        "track_order.html",
        order=order,
        order_items=order_items
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, password)
        ):
            session["admin_logged_in"] = True
            return redirect("/admin/orders")

        return render_template(
            "admin_login.html",
            error="Invalid username or password."
        )

    return render_template("admin_login.html")


@app.route("/admin/orders")
def admin_orders():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    execute_query(
        cursor,
        "SELECT * FROM orders ORDER BY id DESC",
        ()
    )
    orders = cursor.fetchall()

    execute_query(
        cursor,
        "SELECT * FROM order_items",
        ()
    )
    order_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_orders.html",
        orders=orders,
        order_items=order_items
    )


@app.route("/admin/order/<int:order_id>")
def admin_order_detail(order_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    execute_query(
        cursor,
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    )
    order = cursor.fetchone()

    execute_query(
        cursor,
        "SELECT * FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    order_items = cursor.fetchall()

    cursor.close()
    conn.close()

    if order is None:
        return "Order not found"

    return render_template(
        "admin_order_detail.html",
        order=order,
        order_items=order_items
    )


@app.route("/admin/update-status/<int:order_id>", methods=["POST"])
def update_status(order_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    status = request.form["status"]

    conn = get_db()
    cursor = conn.cursor()

    execute_query(
        cursor,
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin/orders")


@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect("/admin/login")


create_tables()

if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)