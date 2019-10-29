import os
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt
from sqlalchemy.sql import text
from datetime import datetime

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

    return render_template("index.html")

@app.route("/search", methods=["GET"])
def search():
    if request.method == 'GET':
        if "fname" in session:

            title = request.args.get("title").lower()
            title = '%' + title + '%'
            books = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :title OR LOWER(isbn) LIKE :title OR LOWER(author) LIKE :title OR year LIKE :title",{"title": title}).fetchall()
            db.commit()
            if book:
                print (books)
                return render_template("search.html", books=books,name=session['fname'])

            return render_template("error.html",error="NO BOOK",name=username)
        else:
            title = request.args.get("title").lower()
            title = '%' + title + '%'
            books = db.execute("SELECT * FROM books WHERE LOWER(title) LIKE :title OR LOWER(isbn) LIKE :title OR LOWER(author) LIKE :title OR year LIKE :title",{"title": title}).fetchall()
            db.commit()
            if book:
                print (books)
                return render_template("search.html", books=books)

            return render_template("error.html",error="NO BOOK")
    return render_templatee("index.html")



@app.route('/book/<int:book_id>')
def book(book_id):
    book = db.execute("SELECT * FROM books WHERE id = :id",{'id' : book_id}).fetchone()
    if book is None :
        return render_template("error.html",error="NO BOOK")
    reviews = db.execute("SELECT fname, date, rating, body FROM reviews JOIN users ON user_id = users.id WHERE book_id = :book_id ORDER BY reviews.id DESC ",{'book_id':book_id}).fetchone()
    db.commit()
    if 'fname' in session:
        print(book)
        username = session["fname"]
        return render_template('book.html',book=book,reviews=reviews,name=username)
        
    return render_template('book.html',book=book,reviews=reviews)




@app.route('/review',methods=['POST'])
def review():
    book_id = request.form.get('book_id')
    book = db.execute("SELECT * FROM books WHERE id = :id",{'id' : book_id}).fetchone()
    reviews = db.execute("SELECT fname, date, rating, body FROM reviews JOIN users ON user_id = users.id WHERE book_id = :book_id ORDER BY reviews.id DESC ",{'book_id':book_id}).fetchall()
    db.commit()
    if "fname" in session:
        fname = session['fname']
        body = request.form.get('body')
        rating = request.form.get('rating')
        date = datetime.date(datetime.now())
        user_id = db.execute("SELECT id FROM users WHERE fname = :fname ",{"fname":fname}).fetchone()
        db.commit()
        user_id = user_id[0]
        if  db.execute("SELECT user_id,book_id  FROM reviews  WHERE user_id=:user_id AND book_id=:book_id",{'user_id':user_id,'book_id':book_id}).rowcount == 1:
            return render_template('book.html',book=book,reviews=reviews,error="CAN NOT REVIEW TWICE!",name=fname)
        db.execute("INSERT INTO reviews (user_id, book_id, date, body, rating) VALUES (:user_id, :book_id,:date, :body, :rating)",{'user_id':user_id,'book_id':book_id, 'date':date ,'body':body,'rating':rating})
        db.commit()
        return redirect(url_for("book",book_id = book_id))
    reviews = db.execute("SELECT fname, date, rating, body FROM reviews JOIN users ON user_id = users.id WHERE book_id = :book_id ORDER BY reviews.id DESC ",{'book_id':book_id}).fetchall()
    db.commit()
    return render_template('book.html',book=book,reviews=reviews,error="LOGIN FIRST!")

@app.route("/signup",methods=['POST','GET'])
def signup():
    if request.method=='POST':
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        email=request.form.get('email')
        password=request.form.get('password')
        if db.execute("SELECT * FROM users WHERE email = :email ",{"email":email}).rowcount == 1 :
            return render_template('login.html',error="USER ALREADY EXIST!")
        db.execute("INSERT INTO users (fname,lname,email,password) VALUES (:fname,:lname,:email,:password)", {"fname":fname,"lname":lname,"email":email,"password":bcrypt.generate_password_hash(password).decode("utf-8")})
        db.commit()
        session['fname'] = fname
        return redirect(url_for("index"))
    return render_template('signup.html',title='REGISTER')


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if db.execute("SELECT * FROM users WHERE email = :email ",{"email":email}).rowcount == 1 :
            user = db.execute("SELECT * FROM users WHERE email=:email",{"email":email}).fetchone()
            dbpassword = user.password
            if bcrypt.check_password_hash(dbpassword,password):
                  fname = user.fname
                  session['fname'] = fname[0]
                  return redirect(url_for("index"))
            return render_template("login.html",error="WRONG PASSWORD!!")
        return render_template('signup.html',title='REGISTER',error="NO USER WITH THAT EMAIL ADDRESS")

    
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('fname',None)
    return redirect(url_for("index"))



































































 