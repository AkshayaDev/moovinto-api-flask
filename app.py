from flask import Flask, request
from flask_restplus import Api, Resource
import pymongo
import bcrypt

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
database = client['moovintodb']
users = database['users']

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
api = Api(app, version='1.0', title='MoovInto API',
    description='A sample API for MoovInto')


@api.route('/login', endpoint='login')
@api.doc(params={'username': 'Username','password': 'Password'})
class Login(Resource):
    @api.doc(responses={401: 'Not Authorized'})
    def post(self):
        if request.get_json():
            data = request.get_json()
            username = data['username']
            password = data['password']

            if not username:
                return {"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}

            if not password:
                return {"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}

            login_user = users.find_one({ "username" : username })

            if login_user:
                hashedpw = login_user['password']
                api_token = login_user['api_token']
                if bcrypt.checkpw(password.encode('utf-8'), hashedpw):
                    return {"success": "true","status_code": 200, "payload": { "api_token": api_token}}
                else:
                    return {"success": "false", "status_code": 401, "payload": {},
                            "error": {"message": "Unauthorized"}}

            else:
                return {"success": "false", "status_code": 401, "payload": {},
                        "error": {"message": "Unauthorized"}}
        else:
            return {"success": "false", "status_code": 401, "payload": {},
                    "error": {"message": "Unauthorized"}}

@api.route('/register', endpoint='register')
@api.doc(params={'username': 'Username','password': 'Password','confpassword': 'Confirm Password'})
class Register(Resource):
    @api.doc(responses={401: 'Not Authorized'})
    def post(self):
        if request.get_json():
            data = request.get_json()
            username = data['username']
            password = data['password']
            confpassword = data['confpassword']

            if all([username, password, confpassword]):
                if password == confpassword:
                    register_user = users.find_one({"username": username})
                    if register_user:
                        return {"success": "false", "status_code": 400, "payload": {},
                                "error": {"message": "User already exists"}}
                    else:
                        pwhashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
                        newuser = {
                            "username": username,
                            "firstname": "",
                            "lastname": "",
                            "email": "",
                            "password": pwhashed,
                            "api_token": "",
                            "user_type": "",
                            "user_status": "",
                            "user_activation_key": "",
                            "remember_token": "",
                            "created_at": "",
                            "updated_at": ""
                        }
                        database.users.insert_one(newuser)
                        return {"success": "true", "status_code": 200, "payload": {"api_token": ""}}

                else:
                    return {"success": "false", "status_code": 400, "payload": {},
                            "error": {"message": "Passwords not matched"}}

            else:
                return {"success": "false", "status_code": 401, "payload": {},
                        "error": {"message": "Unauthorized"}}

if __name__ == '__main__':
    app.run(debug=True)