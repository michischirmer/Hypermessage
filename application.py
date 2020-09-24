import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# keep track of the state of the index page and the password change
state = 0  # 0 for nothing, 1 for SOLD, 2 for BOUGHT


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session['user_id']

    global state
    s = state
    state = 0

    # gets the amount of cash a user still has left
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id=user_id)[0]['cash']

    # get a list of stocks a user owns
    stocks = db.execute("SELECT * FROM [holdings] WHERE user_id=:id ORDER BY quote", id=user_id)

    # get the price to where you recently bought it
    prices = db.execute("SELECT quote, price FROM [transaction] WHERE user=:id GROUP BY quote ORDER BY date;", id=user_id)

    # add up the amount of money made by the user so far
    total = cash

    dic = []

    for row in stocks:
        name = lookup(row['quote'])['name']
        price = lookup(row['quote'])['price']
        shares = row['shares']
        added = price * shares
        symbol = lookup(row['quote'])['symbol']
        total += added

        for row in prices:
            if symbol == row['quote']:
                change = (price - row['price']) / row['price']

        dic.append({"name": name, "symbol": symbol, "price": price, "shares": shares, "change": change, "change_str": change, "sum": added})

    total = usd(total)
    for row in dic:
        row['price'] = usd(row['price'])
        row['sum'] = usd(row['sum'])
        row['change_str'] = "{:.2f}%".format(row['change_str']);

    dic = sorted(dic, key=lambda x: x['name'])

    # TODO add the state condition

    return render_template("index.html", stocks=dic, total=total, cash=usd(cash), s=s)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        # check for valid stock symbol
        symbol = lookup(request.form.get("symbol"))
        if not symbol:
            return apology("Stock not found")

        # check for positive stock here
        shares = request.form.get("shares")
        try:
            amount = int(shares)
        except ValueError:
            return apology("Enter a Number of Shares")
        if amount <= 0:
            return apology("Shares must be a positive integer")

        # check how much money the user has
        user_id = session['user_id']
        price = symbol['price']
        cash = db.execute("SELECT cash FROM users WHERE id = :id;", id=user_id)
        user_money = (cash[0])['cash']
        if user_money < amount * price:
            return render_template("buy.html", found=False)
        else:
            # subtract money payed for transaction
            user_money -= amount * price

        # update cash money of user
        db.execute("UPDATE users SET cash=:cash WHERE id = :id", id=user_id, cash=user_money)

        result = db.execute("SELECT * FROM [holdings] WHERE user_id=:user_id AND quote=:quote;",
                            user_id=user_id, quote=request.form.get("symbol"))
        if len(result) == 0:
            # it is a new stocking
            # add the transaction to the DB
            db.execute("INSERT INTO [transaction] ([user], [quote], [shares], [price]) VALUES (?, ?, ?, ?);",
                       user_id, symbol['symbol'], amount, price)
            db.execute("INSERT INTO [holdings] ([user_id], [quote], [shares]) VALUES (?, ?, ?);",
                       user_id, symbol['symbol'], amount)
        else:
            # there is already a stock of this company in the users account
            added = result[0]['shares'] + amount
            db.execute("INSERT INTO [transaction] ([user], [quote], [shares], [price]) VALUES (?, ?, ?, ?);",
                       user_id, symbol['symbol'], amount, price)
            db.execute("UPDATE [holdings] SET shares=:shares WHERE user_id=:user_id AND quote=:quote;",
                       shares=added, user_id=user_id, quote=request.form.get("symbol"))

        # change the state to BOUGHT
        global state
        state = 2

        return redirect("/")


@app.route("/history")
@login_required
def history():
    user_id = session['user_id']
    stocks = db.execute("SELECT * FROM [transaction] WHERE user=:user_id ORDER BY date DESC", user_id=user_id)
    for row in stocks:
        if row['quote'] == 'CASH':
            row['name'] = 'CASH'
            row['price'] = usd(row['price'])
            row['quote'] = ''
        else:
            row['name'] = lookup(row['quote'])['name']
            row['price'] = usd(row['price'])

    return render_template("history.html", stocks=stocks)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            # return apology("invalid username and/or password", 403)
            return render_template("login.html", error=True)

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
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        if symbol == "":
            return apology("Please enter a stock symbol")

        results = lookup(symbol)
        if not results:
            return render_template("quote.html", found=False)

        # return the value page for the stock
        return render_template("quote_result.html", result=results)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")

        # user did not provide a name, a password or a confirmation password
        if not name or not password or not request.form.get("confirmation"):
            return apology("You must provide an input!")

        # user did not provide to identical passwords
        if password != request.form.get("confirmation"):
            return apology("Passwords must be the same.")

        if db.execute("SELECT username FROM users WHERE username=:username;", username=name):
            return apology("Username is already taken. Please choose another.")

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password);",
                   username=name, password=generate_password_hash(password))
        return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        user_id = session['user_id']
        stocks = db.execute("SELECT * FROM [holdings] WHERE user_id=:user", user=user_id)

        options = []
        for row in stocks:
            if row['quote'] not in options:
                options.append(row['quote'])

        return render_template("sell.html", stocks=options)
    else:

        user_id = session['user_id']
        stocks = db.execute("SELECT * FROM [holdings] WHERE user_id=:user", user=user_id)

        dic = {}
        options = []
        for row in stocks:
            if row['quote'] not in options:
                options.append(row['quote'])
                dic[row['quote']] = row['shares']
            else:
                dic[row['quote']] += row['shares']
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        price = (lookup(symbol))['price']

        try:
            amount = int(shares)
        except ValueError:
            return apology("Enter a Number of Shares")
        if amount <= 0:
            return apology("Shares must be a positive integer")

        # if the user has not that many shares, raise an apology
        if dic[symbol] < amount:
            return apology("You don't have that many shares")

        # add a transaction to the DB and update the holdings DB
        db.execute("INSERT INTO [transaction] (user, quote, shares, price) VALUES (:user, :quote, :shares, :price);",
                   user=user_id, quote=symbol, shares=-amount, price=price)

        # if there are no stocks left, remove the holding from the DB
        if (dic[symbol] - amount) == 0:
            db.execute("DELETE FROM [holdings] WHERE user_id=:user_id AND quote=:quote", user_id=user_id, quote=symbol)
        else:
            db.execute("UPDATE [holdings] SET shares=:shares WHERE user_id=:user_id AND quote=:quote",
                       shares=(dic[symbol] - amount), user_id=user_id, quote=symbol)

        # update the users cash
        cash = db.execute("SELECT cash FROM [users] WHERE id=:user_id", user_id=user_id)
        db.execute("UPDATE [users] SET cash=:cash WHERE id=:user_id;", cash=((cash[0])['cash'] + amount * price), user_id=user_id)

        # change the state to SOLD
        global state
        state = 1
        return redirect("/")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return render_template("profile.html", state=0)
    else:
        old_password = request.form.get("password")
        confirmation_password = request.form.get("confirmation")
        new_password = request.form.get("new_password")

        # check if old_password is the right password
        result = db.execute("SELECT hash FROM [users] WHERE id=:user_id", user_id=session['user_id'])
        if not check_password_hash(result[0]['hash'], old_password):
            return render_template("profile.html", state=1)
            # show error on profile page

        # update the password in the DB
        db.execute("UPDATE [users] SET hash=:hashn WHERE id=:user_id",
                   user_id=session['user_id'], hashn=generate_password_hash(new_password))
        return render_template("profile.html", state=2)
        # show success on profile page


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "GET":
        return render_template("add_cash.html")
    else:
        global state
        state = 3

        try:
            amount = round(float(request.form.get("text")), 2)
        except ValueError:
            return apology("No valid amount of cash")

        # get the amount of current cash and add it to the received new cash amount
        cash = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session['user_id'])
        cash = amount + cash[0]['cash']
        # amount += cash[0]['cash']

        # update the DB for the new cash
        db.execute("UPDATE users SET cash=:cash WHERE id=:user_id", cash=cash, user_id=session['user_id'])

        # add a transaction to the DB for the new cash
        db.execute("INSERT INTO [transaction] ([user], [quote], [shares], [price]) VALUES (?, ?, ?, ?);",
                       session['user_id'], "CASH", 1, amount)

        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)