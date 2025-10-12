from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'mentor' or 'student'
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    expertise = db.Column(db.Text)  # For mentors
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    mentor_sessions = db.relationship('Session', foreign_keys='Session.mentor_id', backref='mentor')
    student_sessions = db.relationship('Session', foreign_keys='Session.student_id', backref='student')
    slots = db.relationship('Slot', backref='mentor_user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
