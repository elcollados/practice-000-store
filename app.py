from flask import Flask, render_template, session, redirect, request
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
import sqlite3
import os

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def get_db():
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        total REAL NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL
    )
    """)

    try:
        conn.execute(
            "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT'Pending'"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


products = [
    {
        "name": "Product 1",
        "price": 500,
        "image": "product1.jpg"
    },
    {
        "name": "Product 2",
        "price": 750,
        "image": "product2.jpg"
    },
    {
        "name": "Product 3",
        "price": 1000,
        "image": "product3.jpg"
    }
]






@app.route("/")
def home():
    return render_template("index.html", products=products)



@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    cart_products = []

    for product_name, quantity in cart.items():

        for product in products:

            if product["name"] == product_name:

                subtotal = product["price"] * quantity

                cart_products.append({
                    "name": product["name"],
                    "price":product["price"],
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



@app.route("/add-to-cart/<product_name>", methods=["POST"])
def add_to_cart(product_name):

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if product_name in cart:
        cart[product_name] += 1
    else:
        cart[product_name] = 1

    session["cart"] = cart
 
    return redirect("/cart")



@app.route("/remove-from-cart/<product_name>", methods=["POST"])
def remove_from_cart(product_name):

    cart = session.get("cart", {})

    if product_name in cart:
        del cart[product_name]

        session["cart"] = cart

        return redirect("/cart")



@app.route("/decrease-quantity/<product_name>", methods=["POST"])
def decrease_quantity(product_name):

    cart = session.get("cart", {})

    if product_name in cart:

        cart[product_name] -= 1

        if cart[product_name] <= 0:
            del cart[product_name]

    session["cart"] = cart

    return redirect("/cart")   



@app.route("/increase-quantity/<product_name>", methods=["POST"])
def increase_quantity(product_name):

    cart = session.get("cart", {})

    if product_name in cart:
        cart[product_name] += 1

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

    for product_name, quantity in cart.items():
        for product in products:

            if product["name"] == product_name:
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

    cursor = conn.execute(
        """
        INSERT INTO orders (name, address, phone, total)
        VALUES(?, ?, ?, ?)
        """,
        (name, address, phone, total)
    )

    order_id = cursor.lastrowid

    for product in cart_products:

        conn.execute(
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

        conn = get_db()

        order = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if order:
            order_items = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?",
                (order_id,)
            ).fetchall()

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
            username == os.getenv("ADMIN_USERNAME") 
            and check_password_hash(os.getenv("ADMIN_PASSWORD_HASH"), password)
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

    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    order_items = conn.execute(
        "SELECT * FROM order_items"
    ).fetchall()

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

    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    order_items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order_id,)
    ).fetchall()

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

    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/orders")



@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect("/admin/login")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)