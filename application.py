from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

app = Flask(__name__, template_folder='templates', static_url_path='/static/', static_folder='static')
app.config['SECRET_KEY'] = 'ines'

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio = SocketIO(app)

@app.route('/')
def index():
	return render_template('./index.html')

@app.route("/login")
def login():
	return render_template("./login.html")

@socketio.on('connected')
def conn(msg):
	return {'data':'Ok'}

@socketio.on('client_message')
def receive_message(data):
	emit('server_message', data, broadcast=True)


# run the server application
if __name__ == '__main__':
	socketio.run(app, debug=True)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
