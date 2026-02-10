from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # No app binding here!

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone=db.Column(db.Integer,unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
