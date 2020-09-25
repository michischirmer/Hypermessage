import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True



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

# state of the index page
state = 0 # 0 for nothing, 1 for recipient not found, 2 for message sent

@app.route("/")
@login_required
def index():
    # user_id = session['user_id']
    global state
    s = state
    state = 0
    return render_template("index.html", state=s)

changed_name = False
delete_all = False
changed_pw = False

states = {
    'changed_name': False,
    'delete_all': False,
    'changed_pw': False,
    'wrong_pw': False
}

@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        global states

        # reset the state
        for key in states:
            states[key] = False

        return render_template("settings.html", states=list(states.values()))
    else:
        # reset the state
        for key in states:
            states[key] = False

        # user wants to change his name
        username = request.form.get('username')
        if username:
            db.execute("UPDATE [users] SET username=:username WHERE id=:id", id=session['user_id'], username=username)
            states['changed_name'] = True
        
        # user wants to delete all mails received by him
        delete = request.form.get('check')
        if delete:
            states['delete_all'] = True
            db.execute("DELETE FROM mails WHERE recipient=:recipient", recipient=session['user_id'])

        # user wants to change his password
        pw = request.form.get('pw-confirmation')
        if pw:
            result = db.execute("SELECT hash FROM users WHERE id=:id", id=session['user_id'])
            if check_password_hash(result[0]['hash'], request.form.get('old_password')):
                # user input the right password
                states['changed_pw'] = True
                db.execute("UPDATE [users] SET hash=:hash WHERE id=:id", id=session['user_id'], hash=generate_password_hash(pw))
            else:
                # user input the wrong password
                states['wrong_pw'] = True

        return render_template("settings.html", states=list(states.values()), username=username)


@app.route("/inbox", methods=['GET', 'POST'])
@login_required
def inbox():
    if request.method == 'GET':
        emails = db.execute("SELECT * FROM mails WHERE recipient=:recipient ORDER BY date DESC;", recipient=session['user_id'])
        ls = []
        for row in emails:
            sender = db.execute("SELECT username FROM users WHERE id=:id", id=row['sender'])
            username = sender[0]['username']
            subject = row['subject']
            date = str(row['date'])
            message = row['message']
            mail_id = row['id']
            read = row['read']

            ls.append([username, subject, date, message, read, mail_id])

        new_mail = False
        old_mail = False
        for row in ls:
            if row[4] == 0:
                new_mail = True
            if row[4] == 1:
                old_mail = True

        return render_template("inbox.html", mails=ls, new_mail=new_mail, old_mail=old_mail)

    else:

        delete = request.form.get('delete')
        read = request.form.get('read')

        if delete:
            # user wants to delete a mail
            db.execute("DELETE FROM mails WHERE id=:mail_id", mail_id=delete)
        elif read:
            s = db.execute("SELECT read FROM mails WHERE id=:id", id=read)
            state = s[0]['read']
            if state == 0:
                db.execute("UPDATE mails SET read=1 WHERE id=:id;", id=read)
            else:
                db.execute("UPDATE mails SET read=0 WHERE id=:id;", id=read)
        
        return redirect('/inbox')
	    

@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    if request.method == "GET":
        return render_template("send.html")
    else:
        global state

        message = request.form.get("message")
        subject = request.form.get("subject")
        recipient = request.form.get("recipient")
        sender_id = session['user_id']

        # get the id from the recipient (if one exists)
        result = db.execute("SELECT id FROM users WHERE username=:name", name=recipient)
        if not result:
            state = 1 # user not found
            return redirect("/")
        
        recipient_id = result[0]['id']
        state = 2

        db.execute("INSERT INTO [mails] ([message], [subject], [recipient], [sender], [date], [read]) VALUES (:message, :subject, :recipient, :sender, :date, 0);", message=message, subject=subject, recipient=recipient_id, sender=sender_id, date=datetime.now().date().strftime('%Y/%m/%d'))
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

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

@app.route("/about")
@login_required
def about():
    return render_template('about.html')

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)