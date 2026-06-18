import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import error, login_required, lookup, usd
from datetime import datetime
import yfinance as yf

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hyderx.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    # Get user ID from the session
    user_id = session["user_id"]

    # Retrieve user's current cash balance
    user_data = db.execute("SELECT u_balance FROM users WHERE u_id = ?", user_id)
    cash = user_data[0]["u_balance"] if user_data else 0

    total = cash
    # Retrieve stock symbols and shares the user owns
    data = db.execute("SELECT symbol, shares FROM portfolio WHERE u_id = ?", user_id)

    for item in data:
        quote = lookup(item["symbol"])
        
        # Check if the quote is valid before using its properties
        if quote and "price" in quote:
            item["price"] = quote["price"]
            item["total"] = float(item["shares"]) * float(item["price"])
            total += item["total"]
        else:
            item["price"] = None
            item["total"] = 0

    # Render the index page with data, cash balance, and total portfolio value
    return render_template("index.html", data=data, cash=cash, total=total)




@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("/buy.html")

    symbol = request.form.get("symbol")
    if not symbol:
        return error("must provide symbol", 400)
    quote = lookup(symbol)
    if not quote:
        return error("incorrect symbol", 400)

    try:
        shares = float(request.form.get("shares"))
    except ValueError:
        return error("invalid input", 400)

    if not shares:
        return error("must input number of shares", 400)
    elif not shares > 0:
        return error("number of shares must be greater than 0", 400)
    elif shares != int(shares):
        return error("number of shares must be an integer", 400)

    data = db.execute("SELECT * FROM users WHERE u_id=(?)", session["user_id"])
    price = float(quote["price"])
    cost = price * shares
    cash = None
    for i in data:
        cash = i["u_balance"]
    if not cash > 0:
        return error("not enough cash", 400)
    if not cash >  cost:
        return error("not enough cash", 400)
    else:
        cash = cash - cost
    db.execute("UPDATE users SET u_balance=(?) WHERE u_id=(?)", cash, session["user_id"])

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    db.execute("INSERT INTO transactions (u_id, symbol, price, shares, type, timestamp) VALUES (?, ?, ?, ?, ?, ?)",session["user_id"], symbol, price, shares, "BUY", dt_string)
    
    try:
        db.execute("INSERT INTO portfolio (u_id, symbol, price, shares) VALUES (?, ?, ?, ?)", session["user_id"], symbol, price, shares)
    except ValueError:
        check_portfolio = db.execute("SELECT * FROM portfolio WHERE u_id=(?) AND symbol=(?)", session["user_id"], symbol) 
        new_shares = int(check_portfolio[0]["shares"]) + int(shares)       
        db.execute("UPDATE portfolio SET shares=(?) WHERE u_id=(?) AND symbol=(?)", new_shares, session["user_id"], symbol)

    stock = yf.Ticker(symbol)
    c_name = stock.info['shortName']
    try:    
        db.execute("INSERT INTO stocks (symbol, last_price, company_name) VALUES (?, ?, ?)", symbol, price, c_name)
    except ValueError:
        pass
    
    return redirect("/")


@app.route("/history")
@login_required
def history():
    
    # user_id = session["user_id"]

    # # Retrieve user's current cash balance
    # user_data = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    # cash = user_data[0]["cash"] if user_data else 0

    # # Retrieve stock symbols and shares the user owns
    # data = db.execute("SELECT symbol, shares FROM bought WHERE user_id = ?", user_id)

    # # Calculate the current price and total value of each stock
    # total = cash
    # for item in data:
    #     quote = lookup(item["symbol"])
    #     item["price"] = quote["price"]
    #     item["total"] = float(item["shares"]) * float(item["price"])
    #     total += float(item["total"])

    # return render_template("history.html",  data=data, cash=cash, total=total)
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE u_name = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["u_hash"], request.form.get("password")
        ):
            return error("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["u_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("/quote.html")

    symbol = request.form.get("symbol")
    if not symbol:
        return error("must provide symbol", 400)
    quote = lookup(symbol)
    if not quote:
        return error("incorrect symbol", 400)
    quote["price"] = usd(quote["price"])
    """Get stock quote."""
    return render_template("/quoted.html", quote=quote)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        try:
            email = request.form.get("email")
        except KeyError:
            email = None

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return error("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return error("must provide password", 400)
        elif not password == confirmation:
            return error("passwords must match", 400)

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (u_name, u_hash, u_email) VALUES(?, ?, ?)", username, hash, email)
        except Exception as e:
            # Check if the error is due to unique constraint
            if "u_name" in str(e):
                return error("Username taken", 400)
            elif "u_email" in str(e):
                return error("Account for this email already exists", 400)
            else:
                return error("Registration failed", 500)

        return redirect("/login")
    """Register user"""
    return render_template("/register.html")
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    id = session["user_id"]

    # Fetch the user's portfolio
    data = db.execute("SELECT * FROM portfolio WHERE u_id = ?", id)

    # Get distinct symbols for dropdown
    symbols = list(set([i["symbol"] for i in data]))

    if request.method == "GET":
        return render_template("/sell.html", symbols=symbols)
    
    else:
        try:
            shares_select = int(request.form.get("shares"))
        except (TypeError, ValueError):
            return error("Invalid number of shares", 400)
        
        symbol_select = request.form.get("symbol")
        if not symbol_select or symbol_select not in symbols:
            return error("Invalid symbol", 400)

        # Fetch the user's available shares for the selected symbol
        user_shares = db.execute(
            "SELECT shares FROM portfolio WHERE u_id = ? AND symbol = ?", id, symbol_select
        )
        if not user_shares:
            return error("Symbol not found in portfolio", 400)

        available_shares = user_shares[0]["shares"]

        # Validate number of shares
        if shares_select <= 0:
            return error("Invalid number of shares", 400)
        if shares_select > available_shares:
            return error("Insufficient shares", 400)

        # Lookup the current price of the symbol
        stock = lookup(symbol_select)
        if not stock:
            return error("Unable to fetch stock price", 400)

        price = stock["price"]
        total_value = price * shares_select

        # Update user's balance
        db.execute(
            "UPDATE users SET u_balance = u_balance + ? WHERE u_id = ?", total_value, id
        )

        # Update portfolio
        if shares_select == available_shares:
            db.execute(
                "DELETE FROM portfolio WHERE u_id = ? AND symbol = ?", id, symbol_select
            )
        else:
            db.execute(
                "UPDATE portfolio SET shares = shares - ? WHERE u_id = ? AND symbol = ?",
                shares_select, id, symbol_select,
            )

        # Record the transaction
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO transactions (u_id, symbol, shares, price, type, date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            id, symbol_select, -shares_select, price, "SELL", now,
        )

        return redirect("/")


