from app.models.user import User
from extentions import db
from werkzeug.security import generate_password_hash
from flask_restful import Resource, reqparse
from flask import g,current_app,request
from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from errors import api_abort


register_reqparser = reqparse.RequestParser()
register_reqparser.add_argument('username', type=str, location='json')
register_reqparser.add_argument('password', type=str, location='json')

login_reqparser = reqparse.RequestParser()
login_reqparser.add_argument('username', type=str, location='json')
login_reqparser.add_argument('password', type=str, location='json')

reset_pwd_reqparser = reqparse.RequestParser()
reset_pwd_reqparser.add_argument('new_pwd', type=str, required=True, location='json')

rename_reqparser = reqparse.RequestParser()
rename_reqparser.add_argument('new_name',type=str, required=True, location='json')


def get_token():
    with current_app.test_request_context():
        token = request.headers.get('Authorization', None)
        if token is None:
            return None

        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(None, 0)
            except ValueError:
                token = None
        else:
            token = None

        token = token.split(';')[0]
        return token


def generate_token(user, expires=3600 * 24 * 7):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires)
    token = s.dumps({'id': user.id}).decode('ascii')
    return token


def validate_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (BadSignature, SignatureExpired):
        return None
    user = User.query.get(data['id'])
    if user is None:
        return None
    # g.current_user = user
    return user


def get_token_info(user):
    token = generate_token(user, 3600 * 24 * 7)
    token_info = {
        'token': 'access_token',
        'expires': 3600 * 24 * 7
    }
    return token_info


def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = get_token()
        if token is None:
            return api_abort(401, 'token is required')
        current_token = token
        return f(*args, **kwargs)

    return decorator


def login_required(f):
    @wraps(f)
    @auth_required(f)
    def decorator(*args, **kwargs):
        current_user = validate_token(g.current_token)

        if current_user is None:
            return api_abort(401, 'invalid_token')

        g.current_user = current_user
        return f(*args, **kwargs)

    return decorator


class RegisterAPI(Resource):
    def POST(self):
        info = register_reqparser.parse_args()
        status = 0
        data = {}
        user = User.query.filter_by(username=info['username']).first()
        if user is not None:
            status = 1
            message = "username already exits"
        else:
            new_user = User(info['username'])
            new_user.set_password(info['password'])
            db.session.add(new_user)
            db.session.commit()
            message = 'register succeed'
            data = {'user_id': new_user.id, 'username': new_user.username}
        return {'status':status, 'message':message, 'data':data}

class LoginAPI(Resource):
    def POST(self):
        info = login_reqparser.parse_args()
        status = 0
        data = {}
        user = User.query.filter_by(username=info['username']).first()
        if user is None:
            status = 1
            message = 'no account'
        elif user is not None and not user.validate_password(info['password']):
            status = 1
            message = 'Invalid username or password'
        else:
            g.current_user = user
            token_info = get_token_info(user)
            message = 'login succeed'
            data = {'username': user.username,'token':token_info}
        return {'status':status, 'message':message, 'data':data}


class ResetPwdAPI(Resource):
    decorators = [login_required]
    def POST(self):
        info = reset_pwd_reqparser.parse_args()
        g.current_user.hash_password = generate_password_hash(info['new_pwd'])
        db.session.commit()
        return {'status': 0, 'message': 'succeed', 'data': {'uid': g.current_user.id, 'username': g.current_user.username}}


class RenameAPI(Resource):
    decorators = [login_required]
    def POST(self):
        info = rename_reqparser.parse_args()
        g.current_user.hash_password = generate_password_hash(info['new_name'])
        db.session.commit()
        return {'status': 0, 'message': 'succeed',
                'data': {'uid': g.current_user.id, 'username': g.current_user.username}}


class LogoutAPI(Resource):
    decorators = [login_required]
    def DELETE(self):
        db.session.delete(g.current_user)
        db.session.commit()
        return {'status': 0, 'message': 'logout success', 'data': {}}

