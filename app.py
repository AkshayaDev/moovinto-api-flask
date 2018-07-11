from flask import Flask, request, jsonify, make_response
from flask_restplus import Api, Resource
from datetime import datetime
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import pymongo
import bcrypt

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
database = client['moovintodb']
users = database['users']

app = Flask(__name__)
# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'super-unique-secret'  # Change this!
jwt = JWTManager(app)
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
                return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}), 400)

            if not password:
                return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}), 400)

            login_user = users.find_one({ "username" : username })

            if login_user:
                hashedpw = login_user['password']
                mongo_id = login_user['_id']
                if bcrypt.checkpw(password.encode('utf-8'), hashedpw):
                    # Identity can be any data that is json serializable
                    access_token = create_access_token(identity = login_user['username'])
                    users.find_one_and_update({"_id": mongo_id},{"$set": {"api_token": access_token}})
                    return make_response(jsonify({"success": "true","status_code": 200, "payload": { "api_token": access_token}}))
                else:
                    return make_response(jsonify({"success": "false", "status_code": 401, "payload": {},
                            "error": {"message": "Unauthorized"}}), 401)

            else:
                return make_response(jsonify({"success": "false", "status_code": 401, "payload": {},
                        "error": {"message": "Unauthorized"}}), 401)
        else:
            return make_response(jsonify({"success": "false", "status_code": 401, "payload": {},
                    "error": {"message": "Unauthorized"}}), 401)

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
                        return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                                "error": {"message": "User already exists"}}), 400)
                    else:
                        pwhashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
                        api_token = create_access_token(identity=username)
                        newuser = {
                            "username": username,
                            "firstname": "",
                            "lastname": "",
                            "email": "",
                            "password": pwhashed,
                            "api_token": api_token,
                            "user_type": "",
                            "user_status": "",
                            "user_activation_key": "",
                            "remember_token": "",
                            "created_at": datetime.now(),
                            "updated_at": datetime.now()
                        }
                        database.users.insert_one(newuser)
                        return make_response(jsonify({"success": "true", "status_code": 200, "payload": {"api_token": api_token}}), 200)

                else:
                    return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                            "error": {"message": "Passwords not matched"}}), 400)

            else:
                return make_response(jsonify({"success": "false", "status_code": 401, "payload": {},
                        "error": {"message": "Unauthorized"}}), 401)

if __name__ == '__main__':
    app.run(debug=True)