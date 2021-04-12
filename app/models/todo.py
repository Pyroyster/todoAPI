from extentions import db,whooshee
from app.models.user import User
from datetime import datetime, date


@whooshee.register_model('task', 'description')
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, db.ForeignKey(User.id))
    task = db.Column(db.String(50))
    description = db.Column(db.String(500))
    done = db.Column(db.Boolean, default=False)
    timeStart = db.Column(db.DateTime, index=True)
    timeOver = db.Column(db.DateTime)

    def __init__(self, task, timeOver, uid):
        self.task = task
        self.timeStart = str(datetime.now())[0:19]
        self.timeOver = timeOver
        self.uid = uid
