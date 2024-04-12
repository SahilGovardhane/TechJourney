
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_sitemapper import Sitemapper
import bcrypt
import requests
import datetime
import bard,os
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ.get("WEATHER_API_KEY")
secret_key = os.environ.get("SECRET_KEY")

app = Flask(__name__)
sitemapper = Sitemapper(app=app) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = secret_key


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode(
            'utf8'), bcrypt.gensalt()).decode('utf8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf8'), self.password.encode('utf8'))


with app.app_context():
    db.create_all()

# Weather Data 


def get_weather_data(api_key: str, location: str, start_date: str, end_date: str) -> dict:
    """
    Retrieves weather data from Visual Crossing Weather API for a given location and date range.

    Args:
        api_key (str): API key for Visual Crossing Weather API.
        location (str): Location for which weather data is to be retrieved.
        start_date (str): Start date of the date range in "MM/DD/YYYY" format.
        end_date (str): End date of the date range in "MM/DD/YYYY" format.

    Returns:
        dict: Weather data in JSON format.

    Raises:
        requests.exceptions.RequestException: If there is an error in making the API request.
    """

    base_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{start_date}/{end_date}?unitGroup=metric&include=days&key={api_key}&contentType=json"

    try:
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print("Error:", e.__str__)
        


@sitemapper.include() 
@app.route('/', methods=["GET", "POST"])
def index():
    """
    Renders the index.html template.

    Returns:
        The rendered index.html template.
    """
    if request.method == "POST":
        global source, destination, start_date, end_date
        source = request.form.get("source")
        destination = request.form.get("destination")
        start_date = request.form.get("date")
        end_date = request.form.get("return")
        no_of_day = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date, "%Y-%m-%d")).days
        if no_of_day < 0:
            flash("Return date should be greater than the Travel date (Start date).", "danger")
            return redirect(url_for("index"))
        else:
            try:
                weather_data = get_weather_data(api_key, destination, start_date, end_date)
            except requests.exceptions.RequestException as e:
                flash("Error in retrieving weather data.{e.Error}", "danger")
                return redirect(url_for("index"))
        
        """Debugging"""
        try:
            plan = bard.generate_itinerary(source, destination, start_date, end_date, no_of_day)
        except Exception as e:
            flash("Error in generating the plan. Please try again later.", "danger")
            return redirect(url_for("index"))
        if weather_data:
            return render_template("dashboard.html", weather_data=weather_data, plan=plan)
    
    return render_template('index.html')

@sitemapper.include() 
@app.route("/about")
def about():
    """
    Renders the about.html template.

    Returns:
        The rendered about.html template.
    """
    return render_template("about.html")

@sitemapper.include()
@app.route("/index1.html")
def index1():
    return render_template("index1.html")

@sitemapper.include()
@app.route("/contact")
def contact():
    """
    Renders the contact.html template.

    Returns:
        The rendered contact.html template.
    """
    user_email = session.get('user_email', "Enter your email")
    user_name = session.get('user_name', "Enter your name")
    message = ''

    return render_template("contact.html", user_email=user_email, user_name=user_name, message=message)

@sitemapper.include() 
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Renders the login.html template.

    Returns:
        The rendered login.html template.
    """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            flash("Login successful.", "success")
            print(session["user_email"])
            return redirect(url_for("index"))
        
        else:
            flash("Wrong email or password. Please try again or register now.", "danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html")

@sitemapper.include() 
@app.route("/logout")
def logout():
    """
    Logs the user out.

    Returns:
        Redirects to the login page.
    """
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# import re

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     """
#     Renders the register.html template and handles user registration.

#     If the request method is GET, the function renders the register.html template.
#     If the request method is POST, the function handles user registration by checking if the passwords match,
#     checking if the user already exists, and adding the user to the database if they don't exist.

#     Returns:
#         If the request method is GET, the rendered register.html template.
#         If the request method is POST and the user is successfully added to the database, a redirect to the login page.
#         If the request method is POST and the passwords don't match or the user already exists, a redirect to the login page with an error message.
#     """
#     if request.method == "POST":
#         name = request.form.get("name")
#         email = request.form.get("email")
#         password = request.form.get("password")
#         password2 = request.form.get("password2")
        
#         # Check if passwords match
#         if password == password2:
#             # Validate email format
#             if not re.match(r"(^[a-zA-Z0-9_.+-]+@(gmail|hotmail|yahoo|edu|apsit)\.(edu\.in|com)$)", email):
#                 flash("Invalid email address. Please enter a valid Gmail, Hotmail, Yahoo, edu, or apsit.edu.in email.", "danger")
#                 return render_template("register.html", error="Invalid email address.")
            
#             # Check if user already exists
#             existing_user = User.query.filter_by(email=email).first()
#             if existing_user:
#                 flash("User already exists. Please log in.", "danger")
#                 return redirect("/login")
#             else:
#                 # Add user to the database
#                 user = User(name=name, email=email, password=password)
#                 db.session.add(user)
#                 db.session.commit()
#                 return redirect("/login")
#         else:
#             flash("Passwords do not match.", "danger")
#             return redirect("/register")
#     else:
#         return render_template("register.html")

import re

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Renders the register.html template and handles user registration.

    If the request method is GET, the function renders the register.html template.
    If the request method is POST, the function handles user registration by checking if the passwords match,
    checking if the user already exists, and adding the user to the database if they don't exist.

    Returns:
        If the request method is GET, the rendered register.html template.
        If the request method is POST and the user is successfully added to the database, a redirect to the login page.
        If the request method is POST and the passwords don't match or the user already exists, a redirect to the login page with an error message.
    """
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        
        # Check if passwords match
        if password == password2:
            # Validate email format
            if not re.match(r"(^[a-zA-Z0-9_.+-]+@(gmail|hotmail|yahoo|edu|apsit)\.(edu\.in|com)$)", email):
                flash("Invalid email address. Please enter a valid Gmail, Hotmail, Yahoo, edu, or apsit.edu.in email.", "danger")
                return render_template("register.html", error="Invalid email address.")
            
            # Check if password length is greater than 6
            if len(password) <= 6:
                flash("Password must be greater than 6 characters long.", "danger")
                return redirect("/register")
            
            # Check if password contains at least one lowercase character
            if not any(char.islower() for char in password):
                flash("Password must contain at least one lowercase character.", "danger")
                return redirect("/register")
            
            # Check if password contains at least one uppercase character
            if not any(char.isupper() for char in password):
                flash("Password must contain at least one uppercase character.", "danger")
                return redirect("/register")
            
            # Check if password contains at least one special character
            if not re.search(r"[^\w\s]", password):
                flash("Password must contain at least one special character.", "danger")
                return redirect("/register")
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("User already exists. Please log in.", "danger")
                return redirect("/login")
            else:
                # Add user to the database
                user = User(name=name, email=email, password=password)
                db.session.add(user)
                db.session.commit()
                return redirect("/login")
        else:
            flash("Passwords do not match.", "danger")
            return redirect("/register")
    else:
        return render_template("register.html")


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')

@app.route("/sitemap.xml")
def r_sitemap():
    return sitemapper.generate()

@app.errorhandler(404)
def page_not_found(e):
    """
    Renders the 404.html template.

    Returns:
        The rendered 404.html template.
    """
    return render_template('404.html'), 404

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}


