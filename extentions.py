from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
import redis

db = SQLAlchemy()
whooshee = Whooshee()
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
