from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy(app)

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    passhash = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    resume_path = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.Date, default=date.today, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    phone_no = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    service = db.relationship('Service', back_populates='professionals')
    requests = db.relationship('Request', back_populates='professional')


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    passhash = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.Date, default=date.today, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    phone_no = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String, nullable=False)
    
    requests = db.relationship('Request', back_populates='customer')


class Request(db.Model):
    req_id = db.Column(db.Integer, primary_key=True)
    date_of_req = db.Column(db.Date, default=date.today, nullable=False)
    date_of_completion = db.Column(db.Date, nullable=True)
    service_status = db.Column(db.String(50), nullable=False)
    service_rating = db.Column(db.Float, nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    
    professional = db.relationship('Professional', back_populates='requests')
    service = db.relationship('Service', back_populates='service_requests')
    customer = db.relationship('Customer', back_populates='requests')


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(50), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    service_description = db.Column(db.String(250), nullable=False)
    image_url = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50),nullable=False)
    professionals = db.relationship('Professional', back_populates='service')
    service_requests = db.relationship('Request', back_populates='service')


with app.app_context():
    db.create_all()
