import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    rows = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)


    #Create a list of all unique symbols and create a list of stock informations (symbols, shares)
    stocks = []
    symbols = []
    for row in rows:
        if row['symbol'] not in symbols:
            symbols.append(row['symbol'])
            info = lookup(row['symbol'])
            stock = {
                'symbol': row['symbol'],
                'shares': row['shares'],
                'price': info['price'],
                'name': info['name']
            }
            stocks.append(stock)
        else:
            for stock in stocks:
                if stock['symbol'] == row['symbol']:
                    stock['shares'] += row['shares']


    #Calculate totals for each stock
    total_sum = 0
    for stock in stocks:
        total = stock['price'] * stock['shares']
        stock['total'] = total
        total_sum += total


    cash = user[0]['cash']
    total_sum += cash


    return render_template("index.html", cash=cash, stocks=stocks, total_sum=total_sum)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get('symbol')
        if not symbol:
            return apology("You must provide a symbol!")
        try:
            stock = lookup(symbol)
            price = stock['price']
        except:
            return apology("Incorrect symbol!")
        shares = request.form.get('shares')
        if not shares:
            return apology("You must enter the number of shares to buy!")
        data = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
        cash = data[0]['cash']
        if cash < price * int(shares):
            return apology("Insufficent funds!")
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)", user_id=session["user_id"], symbol=symbol.upper(), shares=shares, price=price)
        db.execute("UPDATE users SET cash=? WHERE id=?", cash - price * int(shares), session["user_id"])
        return redirect("/")

@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT * FROM transactions WHERE user_id=?", session["user_id"])
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
        return render_template("quote.html")
    else:
        symbol = request.form.get('symbol')
        try:
            stock = lookup(symbol)
            return render_template("quoted.html", stock=stock)
        except:
            return apology("Invalid Symbol")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        username = request.form.get('username')
        if not username:
            return apology("You must provide a username!!!")
        password1 = request.form.get('password1')
        if not password1:
            return apology("You must enter a password!!!")
        password2 = request.form.get('password2')
        if not password2:
            return apology("You must retype your password!!!")
        if password1 != password2:
            return apology("Your passwords do not match!!!")
        hash = generate_password_hash(password1)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)
        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        user_id = session['user_id']
        rows = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)


        #Create a list of all unique symbols and create a list of stock informations (symbols, shares)
        stocks = []
        symbols = []
        for row in rows:
            if row['symbol'] not in symbols:
                symbols.append(row['symbol'])
                stock = {
                    'symbol': row['symbol'],
                    'shares': row['shares']
                }
                stocks.append(stock)
            else:
                for stock in stocks:
                    if stock['symbol'] == row['symbol']:
                        stock['shares'] += row['shares']


        return render_template("sell.html", stocks=stocks)


    else:
        user_id = session['user_id']
        symbol = request.form.get('symbol')
        if not symbol:
            return apology('You need to select a symbol!!!')
        shares = request.form.get('shares')
        if not shares:
            return apology('You need to enter the number of shares!!!')
        user_id = session["user_id"]
        rows = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)


        #Create a list of all unique symbols and create a list of stock informations (symbols, shares)
        stocks = []
        symbols = []
        for row in rows:
            if row['symbol'] not in symbols:
                symbols.append(row['symbol'])
                stock = {
                    'symbol': row['symbol'],
                    'shares': row['shares']
                }
                stocks.append(stock)
            else:
                for stock in stocks:
                    if stock['symbol'] == row['symbol']:
                        stock['shares'] += row['shares']


        for stock in stocks:
            if stock['symbol'] == symbol:
                if stock['shares'] < int(shares):
                    return apology("Too many shares!!!")


            stock = lookup(symbol)
            amount = int(shares) * stock['price']
        db_cash = db.execute('SELECT cash FROM users WHERE id=?', user_id)
        new_cash = db_cash[0]['cash'] + amount
        db.execute('UPDATE users SET cash=? WHERE id=?', new_cash, user_id)
        db.execute('INSERT INTO transactions (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)', user_id=user_id, symbol=symbol, shares=-1*int(shares), price=stock['price'])
        flash('Sold')
        return redirect('/')


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
