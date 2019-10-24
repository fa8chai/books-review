import os
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt
from sqlalchemy.sql import text


app = Flask(__name__)

bcrypt = Bcrypt(app)




app.secret_key= b'\xe8:[\x8cu\xcc\xb7P\x1a\x13\xd0\xa4\xd9\xaci\x89'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if "fname" in session:
        username = session["fname"]

    return render_template("index.html",name=username)


@app.route("/signup",methods=['POST','GET'])
def signup():
    if request.method=='POST':
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        email=request.form.get('email')
        password=request.form.get('password')
        if db.execute("SELECT * FROM users WHERE email = :email ",{"email":email}).rowcount == 1 :
            return "already exists!!"
        db.execute("INSERT INTO users (fname,lname,email,password) VALUES (:fname,:lname,:email,:password)", {"fname":fname,"lname":lname,"email":email,"password":bcrypt.generate_password_hash(password)})
        db.commit()
        return render_template('reg.html')
    return render_template('signup.html',title='REGISTER')


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if db.execute("SELECT * FROM users WHERE email = :email ",{"email":email}).rowcount == 1 :
    
            fname = db.execute(text("SELECT fname FROM users WHERE email = :email",{"email":email})).fetchone()
            session["fname"]= fname
            return redirect(url_for("index"))
        return "not req"
    return render_template("login.html")






























































 