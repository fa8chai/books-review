import os
from flask import Flask, session, render_template, request, redirect, url_for,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt
from sqlalchemy.sql import text
from datetime import datetime
import requests

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo,Length


class RegistrationForm(FlaskForm):
    fname = StringField('Username',validators= [DataRequired(message="Please enter a username"),Length(min=4, max=18,message="username must be between 4 and 18 characters long")])
    lname = StringField('Full Name', validators=[DataRequired(message="Please enter your full name"),Length(min=6, max=25)])
    email = StringField('Email Address',validators= [DataRequired(message="Please enter your email"),Email(message=('That is not a valid email address'))])
    password = PasswordField('New Password',validators= [DataRequired(message="Please enter a password"),Length(min=8, max=20,message="Password must be between 8 and 20 characters long")])
    submit = SubmitField('Register')


    def validate_fname(form, field):
        if db.execute("SELECT * FROM users WHERE fname = :fname ",{"fname":field.data}).rowcount == 1 :
            raise ValidationError(f'{field.data} aleady taken')

    def validate_email(form, field):
         if db.execute("SELECT * FROM users WHERE email = :email ",{"email":field.data}).rowcount == 1 :
             raise ValidationError('email address already exists')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Please enter your email"),Email(message=('That is not a valid email address'))])
    password = PasswordField('Password', validators=[DataRequired(message="Please enter your password")])
    submit = SubmitField('Login')

    def validate_email(form,field):
        if db.execute("SELECT * FROM users WHERE email = :email ",{"email":field.data}).rowcount == 0 :
            raise ValidationError('Email not registered')



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


@app.route('/api/<isbn>',methods=['GET'])
def api(isbn):
    isbn = isbn
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",{'isbn' : isbn}).fetchone()
    db.commit()
    #print(jsonify(book))
    if book is None:
        res = {
           "error_code": 404,
           "error_message": "Not Found" 
        }, 404
        return jsonify(res)
    res = db.execute("SELECT  title ,author,year,isbn,COUNT(reviews.id) as review_count ,AVG(reviews.rating) as average_score FROM books  LEFT JOIN reviews ON books.id = book_id WHERE isbn=:isbn GROUP BY title ,author,year,isbn ",{'isbn':isbn}).fetchone()
    db.commit()
    print(res)
   
    resbook = {
          "title": res.title,
          "author": res.author,
          "year": res.year,
          "isbn": isbn,
          "review_count": res.review_count,
          "average_score": res.average_score
     }
    return jsonify(resbook)


 
 




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
    db.commit()
    if book is None :
        return render_template("error.html",error="NO BOOK")
    reviews = db.execute("SELECT fname, date, rating, body FROM reviews JOIN users ON user_id = users.id WHERE book_id = :book_id ORDER BY reviews.id DESC ",{'book_id':book_id}).fetchone()
    db.commit()
    
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "s18kbfQ47SeAy9WFej1gBA", "isbns": book.isbn})

    print(res.json())
    res = res.json()
    number_of_ratings = res['books'][0]['work_ratings_count']
    average_rating = res['books'][0]['average_rating']
       
    
    
    
    if 'fname' in session:
        print(book)
        username = session["fname"]
        return render_template('book.html',book=book,reviews=reviews,name=username,nrating=number_of_ratings,arating=average_rating)
        
    return render_template('book.html',book=book,reviews=reviews,nrating=number_of_ratings,arating=average_rating ,error="LOGIN FIRST!")




@app.route('/review',methods=['POST'])
def review():
    book_id = request.form.get('book_id')
    book = db.execute("SELECT * FROM books WHERE id = :id",{'id' : book_id}).fetchone()
    reviews = db.execute("SELECT fname, date, rating, body FROM reviews JOIN users ON user_id = users.id WHERE book_id = :book_id ORDER BY reviews.id DESC ",{'book_id':book_id}).fetchall()
    db.commit()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "s18kbfQ47SeAy9WFej1gBA", "isbns": book.isbn})
    res = res.json()
    number_of_ratings = res['books'][0]['work_ratings_count']
    average_rating = res['books'][0]['average_rating']
       
    if "fname" in session:
        fname = session['fname']
        body = request.form.get('body')
        rating = request.form.get('rating')
        date = datetime.date(datetime.now())
        user_id = db.execute("SELECT id FROM users WHERE fname = :fname ",{"fname":fname}).fetchone()
        db.commit()
        user_id = user_id[0]
        if  db.execute("SELECT user_id,book_id  FROM reviews  WHERE user_id=:user_id AND book_id=:book_id",{'user_id':user_id,'book_id':book_id}).rowcount == 1:
            return render_template('book.html',book=book,reviews=reviews,error="CAN'T REVIEW TWICE!",name=fname,nrating=number_of_ratings,arating=average_rating )
        db.execute("INSERT INTO reviews (user_id, book_id, date, body, rating) VALUES (:user_id, :book_id,:date, :body, :rating)",{'user_id':user_id,'book_id':book_id, 'date':date ,'body':body,'rating':rating})
        db.commit()
        return redirect(url_for("book",book_id = book_id))
    return redirect(url_for("book",book_id = book_id))





@app.route("/signup",methods=['POST','GET'])
def signup():
    form = RegistrationForm()
    if request.method =='POST' and form.validate_on_submit() :
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        email=request.form.get('email')
        password=request.form.get('password')
        db.execute("INSERT INTO users (fname,lname,email,password) VALUES (:fname,:lname,:email,:password)", {"fname":fname,"lname":lname,"email":email,"password":bcrypt.generate_password_hash(password).decode("utf-8")})
        db.commit()
        session['fname'] = fname
        return redirect(url_for("index"))
    return render_template('signup.html',title='REGISTER',form = form)


@app.route("/login",methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method=='POST' and form.validate_on_submit() :
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.execute("SELECT * FROM users WHERE email=:email",{"email":email}).fetchone()
        dbpassword = user.password
        if not bcrypt.check_password_hash(dbpassword,password):
            return render_template("login.html",form=form,perror="Password is incorrect")
        fname = user.fname
        session['fname'] = fname[0]
        return redirect(url_for("index"))
    return render_template("login.html",form=form)

@app.route('/logout')
def logout():
    session.pop('fname',None)
    return redirect(url_for("index"))



































































 