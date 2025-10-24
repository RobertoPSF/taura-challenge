from . import db
import uuid
from sqlalchemy import func

class Scan(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="scanning")
    urls_found = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())
    completed_at = db.Column(db.DateTime)
    
class Finding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.String, db.ForeignKey("scan.id"))
    data = db.Column(db.JSON)
