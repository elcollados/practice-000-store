Flask(__name__) creates the web app. (call the HTML file using app.route()).
render_template("index.html", products=products) shows an HTML page and sends data into it. (the data = products=products)
session["cart"] keeps one separate memory (dictionary) per visitor, stored in a signed cookie. (to have each their own cart data).
redirect("/cart") sends the visitor to another page. (the /cart means sends to cart page).
request.form["name"] reads the data the visitor sent in a form. (form in html like <form><input>/<button></form>).
CSRFProtect(app) check every POST/PUT/PATCH/DELETE request for a valid csrf_token, and block it if missing or wrong.
load_dotenv() reads the .env file and loads its values as enviroment variables, (you create the .env file. separate the secret info). 
os.getenv("name") returns the value of an environment variable, or None if it does not exist.(to read the saparated environment).
check_password_hash(saved_hash, typed_password) returns True if typed password matches the saved hash, otherwise False.(to prevent from seeing the secret info)
sqlite.connect("store.db") opens the local SQLite database files (used for testing on my PC).
conn.row_factory = sqlite3.Row lets SQLite rows be read by column name like row["name"].(easy to read and safer when we do changes).
psycopg2.connect(database_url, cursor_factory=DictCursor) conencts to the PostgreSQL database on Render, with rows readable by column name.
conn.cursor() creates the object that runs queries.(conn the open line to the database, cursor the tool on that line sends a query and holds the result)
cursor.execute(query, values) runs one SQL query with the values filled placeholder. (query and values must be same count).
cursor.fetchone() returns one row (or None ), cursor.fetchall() returns a list of all matching rows.(use fetchone for less code).
conn.commit() saves the changes (INSERT,UPDATE) to the database.(its okay if no changes).
conn.close() closes the connection between Flask app and the database.
app.secret_key = SECRET_KEY is the key Flask uses to sign the cookie, so nobody can change the cart or fake a login.
raise RuntimeError("message") stops the app from starting and shows the message. used it when SECRET_KEY or admin login is missing. 
@app.route("/cart") connects a web address to the function below it. (opening the cart with the total).
method=["POST"] send data to the website to do something (save, chnage, delete). it can carry visitor data.
/product/<int:product_id> shows one product alone, if the product does not exist, it returns "Product not found" (404).
session.get("cart", {}) return the cart, or an empty dictionary if there is no cart yet.(the visitor never added anything, or the cart was cleared).
session.pop("cart", None) delete the cart from session.(session=visitor's browser)(pop=remove)
request.form.get("quantity", 1) gets the product quantity from the add-to-cart form. if the form sent no product quantity, it uses 1.
.strip() removes extra spaces at the end of the text.
.isdigit() returns true the text has digits only. I use it to check the phone number
return "product not found", 404 sends a message with the 404(not found) status.
if "cart" not in session checks if the visitor has no cart yet.
SELECT * FROM products ORDER BY id gets all products, sorted by id.(1,2,3...)
SELECT COUNT(*) FROM products counts the rows. if it is 0, I add the 3 default products.(product name, price, image).
INSESRT INTO products (name, price, image) VAUES (?, ?, ?) add a new row to the products table in database, using the 3 values I pass in.
UPDATE orders SET status = ? WHERE id = ? changes the status of the one order with that id. change to shipped the id 1 product.
RETURNING id (PostgreSQL) gives back the id of the new row, and cursor.latrowid (SQLite) does the same job. I need this id to save the order items under right order.
f"""...{id_column} ...""" puts the variable inside the text. I use it so the id column is defferent for SQLite and PostgreSQL.
query.replace("?", "%s") changes every ? in the query to %s. It only runs when DATABASE_URL exist (PostgreSQL), because SQLite uses ? and PostreSQL uses %s.
session["admin_logged_in"] = true remembers that the admin logged in.
if not session,get("admin_logged_in") blocks the page and sends the visitor to the login page.
app.run(debug=DEBUG_mMODE) starts the website, debug mode is off by default, to turn it on locally, set FLASK_DEBUG=1 in .env. It is for my PC only. On Render it stay off, so visitor cannot see my code in error pages.
if __name__ == "__main__": runs the code below only when I start this file directly.