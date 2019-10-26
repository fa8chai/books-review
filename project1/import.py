import csv

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
engine = create_engine("postgres://emgdsajodfvbll:122fb58a5750a5c7702f00ca0c33f9a10acb702e86d10aaede168e54b49e3b9a@ec2-46-137-113-157.eu-west-1.compute.amazonaws.com:5432/d133i8nospr2lp")
db = scoped_session(sessionmaker(bind=engine)) 


f = open("books.csv")
reader = csv.reader(f)
next(reader, None)

for isbn,title,author,year in reader :
    db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn, :title, :author, :year)",{'isbn':isbn,'title':title,'author':author,'year':year})
    print(1)
    db.commit()