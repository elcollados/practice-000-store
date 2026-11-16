# Store Website

A simple online store built with Flask. Customers can browse products, add them to a cart, place an order, and track it. An admin can log in to view orders and update their status.

Live demo: https://store-website-2niw.onrender.com

## Features

 Product list and product detail pages
- Shopping cart (add, remove, increase, decrease, clear)
- Checkout and order placement
- Order tracking with order ID and phone number
- Admin login, order list, order details, and status update
- CSRF protection on forms
- Admin password stored as a hash, not plain text

## Tech Used

- Python, Flask
- SQLite (local) and PostgreSQL (Render)
- HTML / Jinja templates
- Deployed on Render

## How to Run Locally

1. Clone the project:
   ```
   git clone https://github.com/elcollados/Store-website.git
   cd Store-website
   ``` 
2. Install the packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file:
   ```
   SECRET_KEY=your-secret-key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD_HASH=your-password-hash
   ```
4. Make a password hash:
   ```
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
   ```
5. Run the app:
   ```
   python app.py
   ```
6. Open `http://127.0.0.1:5000`

If `DATABASE_URL` is set, the app uses PostgreSQL. If not, it uses a local SQLite file (`store.db`).

## How This Was Built

- Most of the code was written with AI assistance (ChatGPT and Claude).
- I retyped the code myself and studied how each part works, as for me to experience the process of building live website.
- What I did myself: [deploying to Render, setting up GitHub, testing, fixing ..., changing ...].
- What I am still learning: [SQL queries, sessions, PostgreSQL vs SQLite].

## Learning notes
See [LEARNING.md](LEARNING.md) for what I learned while building this project, I still have a lot of needs to learn, I only added the new word codes that I used in this project.