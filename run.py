from flask import Flask
from flask_restful import Api
import os
from extentions import db, whooshee
# 导入各资源类
from app.resources.todo import TodoAPI, TodoListAPI
from app.resources.auth import RegisterAPI, LoginAPI, ResetPwdAPI, RenameAPI, LogoutAPI

app = Flask(__name__)
ctx = app.app_context()
ctx.push()
app.secret_key = os.urandom(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:210421@localhost/todo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['KEY_ACCESS_TOKEN'] = 'access_token'
# app.config['KEY_REFRESH_TOKEN'] = 'refresh_token'
app.config['ACCESS_TOKEN_EXPIRES'] = 3600 * 24 * 7
# app.config['REFRESH_TOKEN_EXPIRES'] = 3600 * 24 * 30

api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


api.add_resource(TodoAPI, '/api/todolist/<int:id>', endpoint='todo')
api.add_resource(TodoListAPI, '/api/todolist', endpoint='todolist')
api.add_resource(RegisterAPI, '/api/user/register')
api.add_resource(LoginAPI, '/api/user/login')
api.add_resource(LogoutAPI, '/api/user/logout')
api.add_resource(ResetPwdAPI, '/api/user/pwd/reset')
api.add_resource(RenameAPI, '/api/user/name/reset')


if __name__ == '__main__':
    db.init_app(app)
    whooshee.init_app(app)
    app.run(port=5000, debug=True)