from flask import request
from flask_restful import Resource, reqparse
from app.models.todo import Task
from flask_login import current_user
from math import floor
from extentions import db, whooshee, pool
from app.resources.auth import login_required, get_token_info
import redis
r = redis.Redis(connection_pool=pool)

post_reqparse = reqparse.RequestParser()
post_reqparse.add_argument('task', type=str, required=True, location='json')
post_reqparse.add_argument('description', type=str, location='json')
post_reqparse.add_argument('timeOver', type=str, required=True, location='json')

put_reqparse = reqparse.RequestParser()
put_reqparse.add_argument('task', type=str, location='json')
put_reqparse.add_argument('description', type=str, location='json')
put_reqparse.add_argument('timeOver', type=str, location='json')


class TodoAPI(Resource):
    decorators = [login_required]

    def get(self, id):
        todo = Task.query.get(id)  # Task.query.filter_by(id=id).first()
        status = 0
        data = {}
        if todo is None:
            status = 1
            message = 'not found'
        elif current_user.id != todo.uid:
            status = 1
            message = 'not allowed'
        else:
            message = 'succeed'
            data = todo_schema(todo)
        return {'status': status, 'message': message, 'data': data}

    def put(self, id):
        todo = Task.query.get(id)  # Task.query.filter_by(id=id).first()
        status = 1
        data = {}
        message = ''
        if todo is None:
            message = 'not found'
        elif current_user.id != todo.uid:
            message = 'not allowed'
        else:
            args = dict(put_reqparse.parse_args())
            update_todo(args, todo)
            db.session.commit()
            status = 0
            message = 'succeed'
            data = todo_schema(todo)
        return {'status': status, 'message': message, 'data': data}

    def patch(self,id):
        todo = Task.query.get(id)  # Task.query.filter_by(id=id).first()
        status = 1
        data = {}
        message = ''
        if todo is None:
            message = 'not found'
        elif current_user.id != todo.uid:
            message = 'not allowed'
        else:
            todo.done = not todo.done
            db.session.commit()
            status = 0
            message = 'succeed'
            data = todo_schema(todo)
        return {'status': status, 'message': message, 'data': data}

    def delete(self, id):
        todo = Task.query.get(id)  # Task.query.filter_by(id=id).first()
        status = 1
        data = {}
        message = ''
        if todo is None:
            message = 'not found'
        elif current_user.id != todo.uid:
            message = 'not allowed'
        else:
            db.session.delete(todo)
            db.session.commit()
            message = 'succeed'
        return {'status': status, 'message': message, 'data': data}


class TodoListAPI(Resource):
    decorators = [login_required]

    def get(self):
        option = int(request.args.get('option', -1))
        if option == -1:
            todolist = Task.query.filter_by(uid=current_user.id).all()
        elif option == 0:
            todolist = Task.query.filter_by(uid=current_user.id, done=False).all()
        elif option == 1:
            todolist = Task.query.filter_by(uid=current_user.id, done=True).all()
        elif option == 2:
            search_str = request.args.get('q', '')
            todolist = Task.query.whooshee_search(search_str).filter_by(uid=current_user.id).all()
            r.lpush('recent_search', search_str)

        data = {
            'list': todolist_schema(todolist),

        }
        page = int(request.args.get("page", 1))
        per_num = int(request.args.get("per_page", 20))
        total = len(todolist)
        pagination_data = {
            'total': total,  # 符合查询的结果个数
            'page': page,  # 当前页数
            'pages': floor(total/per_num)+1,  # 总页数
            'have_next': True if total > page*per_num else False,
            'have_prev': True if page != 1 else False,
        }
        data.update(pagination_data)
        return {'status': 0, 'message': 'succeed', 'data': data}

    def post(self):
        args = post_reqparse.parse_args()
        new_todo = Task(task=args['task'], timeOver=args['timeOver'], uid=current_user.id)
        if 'description' in args:
            new_todo.description = args['description']
        db.session.add(new_todo)
        db.session.commit()
        todo = Task.query.filter_by(uid=current_user.id).first()
        data = todo_schema(todo)
        return {'status': 0, 'message': 'succeed', 'data': data}

    def put(self):
        option = int(request.args.get('option', 0))
        if option == 0:
            todolist = Task.query.filter_by(uid=current_user.id).all()
        elif option == 1:
            todolist = Task.query.filter_by(uid=current_user.id, done=False).all()
        for todo in todolist:
            todo.done = not todo.done
        db.session.commit()
        data = todolist_schema(todolist)
        return {'status': 0, 'message': 'succeed', 'data': data}

    def delete(self):
        option = int(request.args.get('option', -1))
        if option == -1:
            todolist = Task.query.filter_by(uid=current_user.id).all()
        elif option == 0:
            todolist = Task.query.filter_by(uid=current_user.id, done=False).all()
        elif option == 1:
            todolist = Task.query.filter_by(uid=current_user.id, done=True).all()
        for todo in todolist:
            db.session.delete(todo)
        db.session.commit()
        data = todolist_schema(todolist)
        return {'status': 0, 'message': 'succeed', 'data': data}


def todo_schema(todo):
    return {
        'uid': todo.uid,
        'task': todo.task,
        'description': todo.description,
        'done': todo.done,
        'timeStart': str(todo.timeStart),
        'timeOver': str(todo.timeOver)
    }


def todolist_schema(todolist):
    data_list = []
    for todo in todolist:
        data_list.append(todo_schema(todo))
    return data_list


def update_todo(args, todolist):
    for todo in todolist:
        if args['task'] is not None:
            todo.task = args['task']
        if args['description'] is not None:
            todo.description = args['description']
        if args['timeOver'] is not None:
            todo.timeOver = args['timeOver']
