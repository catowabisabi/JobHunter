from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.orm import class_mapper
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

class Serializer(object):
    """Utility for serializing SQLAlchemy objects."""
    def to_dict(self):
        # Convert the object to a dictionary, excluding SQLAlchemy's internal state
        result = {}
        for c in class_mapper(self.__class__).columns:
            result[c.key] = getattr(self, c.key)
        return result

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PersonalInfo(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    preferred_name = db.Column(db.String(50))
    title = db.Column(JsonEncodedDict)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(200))
    willing_to_relocate = db.Column(JsonEncodedDict)
    portfolio = db.Column(db.String(200))
    behance_portfolio = db.Column(db.String(200))
    github = db.Column(db.String(200))
    linkedin = db.Column(db.String(200))
    languages = db.Column(JsonEncodedDict)
    summary = db.Column(db.Text)
    design_philosophy = db.Column(db.Text)
    skills = db.Column(JsonEncodedDict)
    professional_attributes = db.Column(JsonEncodedDict)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields from cv.json
    awards_and_recognitions = db.Column(JsonEncodedDict)
    publications = db.Column(JsonEncodedDict)
    references = db.Column(db.Text)
    possible_titles = db.Column(JsonEncodedDict)
    cover_letter_templates = db.Column(JsonEncodedDict)


class Experience(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    period_start = db.Column(db.String(50), nullable=False)
    period_end = db.Column(db.String(50))
    responsibilities = db.Column(JsonEncodedDict)
    highlights = db.Column(JsonEncodedDict)


class Education(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    institution = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    period = db.Column(db.String(100))
    graduated_with_distinction = db.Column(db.Boolean, default=False)
    highlights = db.Column(JsonEncodedDict)


class JobApplication(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    cv_path = db.Column(db.String(200))
    cover_letter_en_path = db.Column(db.String(200))
    cover_letter_zh_path = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending') 