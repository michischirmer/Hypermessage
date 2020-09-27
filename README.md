# Hypermessage

Final project for Harvard's [CS50x](https://cs50.harvard.edu/x/2020/) Course in 2020.

### What is Hypermessage?

Hypermessage is a Simple Web Application for communicating between registered users.

### Create a free Account for Hypermessage

Feel free to sign up for a free acount on the main Weppage. Just pick a unused username and choose a password of your choice.

## Dependencies
Hypermessage requires an installed Python distribution, recommended the lastest one (Version >3), but also supports versions Python 2.7 and PyPy.
All other dependencies are stored in [`requirements.txt`](https://pip.readthedocs.org/en/1.1/requirements.html) at the root of the project and can be installed using ```pip install -r requirements.txt``` 
In specific:
* cs50
* Flask
* Flask-Session
* requests

By installing Flask using ```pip install Flask```you will also install the following distributions:
* [Werkzeug](https://palletsprojects.com/p/werkzeug/) implements WSGI server.
* [Jinja](https://palletsprojects.com/p/jinja/) is a template language that renders the pages your application serves.
* [MarkupSafe](https://palletsprojects.com/p/markupsafe/) comes with Jinja and escapes untrusted input when rendering templates.
* [ItsDangerous](https://palletsprojects.com/p/itsdangerous/) securely signs data to ensure its integrity.
* [Click](https://palletsprojects.com/p/click/) is a framework for writing command line applications.

## Installing

* Download this repo from [https://github.com/michischirmer/Hypermessage.git](https://github.com/michischirmer/Hypermessage.git)
* Clone this repo by using ``` git clone https://github.com/michischirmer/Hypermessage.git```

### Executing program


* Use ```python app.py```
or
* ```flask run``` in the project directory 
to start the development flask server 
* Open ```127.0.0.1:5000``` or ```localhost:5000``` in your browser to interact with the server. <br><br>
To make the server available public at ```0.0.0.0:5000```use ```flask run --host=0.0.0.0```instead.


## Author

Michael Schirmer
* [Facebook](https://www.facebook.com/michael.schirmer.9843/)
* [GitHub](https://github.com/michischirmer)


## Acknowledgments

Code snippets, CSS library, etc.
* [Bootstrap](https://getbootstrap.com)
* [Stack Overflow](https://stackoverflow.com)
* [W3Schools](https://www.w3schools.com)
