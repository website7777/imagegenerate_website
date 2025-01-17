from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    requests = db.relationship("Request", backref="user", lazy=True)

    # Flask-Login requires these methods
    def is_active(self):
        return True  # All users are active by default

    def get_id(self):
        return str(self.id)

# Add this new class
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.String(500), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)