from flask import Flask, request, jsonify, make_response
from flask_restplus import Api, Resource
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
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
@api.doc(params={'email': 'Email','password': 'Password'})
class Login(Resource):
    @api.response(200, 'Success')
    @api.response(401, 'Not Authorized')
    @api.response(400, 'Validation error')
    def post(self):
        if request.get_json():
            data = request.get_json()
            email = data['email']
            password = data['password']

            if not email:
                return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}), 400)

            if not password:
                return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                        "error": {"message": "Field cannot be empty"}}), 400)

            if email:
                try:
                    v = validate_email(email)  # validate and get info
                    email = v["email"]  # replace with normalized form
                except EmailNotValidError as e:
                    # email is not valid, exception message is human-readable
                    return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                                  "error": {"message": str(e)}}), 403)

            login_user = users.find_one({ "email" : email })

            if login_user:
                hashedpw = login_user['password']
                mongo_id = login_user['_id']
                if bcrypt.checkpw(password.encode('utf-8'), hashedpw):
                    # Identity can be any data that is json serializable
                    access_token = create_access_token(identity = login_user['email'])
                    users.find_one_and_update({"_id": mongo_id},{"$set": {"api_token": access_token}})
                    login_payload = {
                        "user_id": login_user['user_id'],
                        "api_token": access_token
                    }
                    return make_response(jsonify({"success": "true","status_code": 200, "payload": login_payload}))
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
@api.doc(params={'email': 'Email','password': 'Password','confpassword': 'Confirm Password'})
class Register(Resource):
    @api.response(200, 'Success')
    @api.response(401, 'Not Authorized')
    @api.response(400, 'Validation error')
    def post(self):
        if request.get_json():
            data = request.get_json()
            email = data['email']
            password = data['password']
            confpassword = data['confpassword']

            if email:
                try:
                    v = validate_email(email)  # validate and get info
                    email = v["email"]  # replace with normalized form
                except EmailNotValidError as e:
                    # email is not valid, exception message is human-readable
                    return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                                  "error": {"message": str(e)}}), 403)

            if all([email, password, confpassword]):
                if password == confpassword:
                    register_user = users.find_one({"email": email})
                    if register_user:
                        return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                                "error": {"message": "User already exists"}}), 400)
                    else:
                        pwhashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
                        api_token = create_access_token(identity=email)
                        new_user_id = database.users.count()+1
                        newuser = {
                            "user_id": new_user_id,
                            "username": "",
                            "firstname": "",
                            "lastname": "",
                            "email": email,
                            "password": pwhashed,
                            "api_token": api_token,
                            "user_type": "",
                            "user_status": "",
                            "user_activation_key": "",
                            "remember_token": "",
                            "created_at": datetime.now(),
                            "updated_at": datetime.now()
                        }
                        # database.users.create_index([('email', pymongo.ASCENDING)],unique = True)
                        # database.users.create_index([('username', pymongo.ASCENDING)],unique = True)
                        # database.users.create_index([('user_id', pymongo.ASCENDING)],unique = True)
                        database.users.insert_one(newuser)
                        register_payload = {
                            "user_id": new_user_id,
                            "api_token": api_token
                        }
                        return make_response(jsonify({"success": "true", "status_code": 200, "payload": register_payload}), 200)

                else:
                    return make_response(jsonify({"success": "false", "status_code": 400, "payload": {},
                            "error": {"message": "Passwords not matched"}}), 400)

            else:
                return make_response(jsonify({"success": "false", "status_code": 401, "payload": {},
                        "error": {"message": "Unauthorized"}}), 401)

@api.route('/user/<int:user_id>')
@api.doc(params={'id': 'An ID', 'API-TOKEN': 'API Token in headers'})
class GetUser(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    def get(self, user_id):
        # check Api token exists
        api_token = request.headers['API-TOKEN']
        if not api_token:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)

        # check api token exists in db
        register_user = users.find_one({"api_token": api_token})

        if register_user:
            register_user_api_token = register_user['api_token']
            register_user_id = register_user['user_id']

            if (register_user_api_token == api_token and register_user_id==user_id):
                user_payload = {
                    "user_id": register_user_id,
                    "username": register_user['username'],
                    "firstname": register_user['firstname'],
                    "lastname": register_user['lastname'],
                    "email": register_user['email'],
                    "user_type": register_user['user_type']
                }
                return make_response(
                    jsonify({"success": "true", "status_code": 200, "payload": user_payload}), 200)
            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)


@api.route('/update-user')
@api.doc(params={'api-token': 'API Token in post data'})
class UpdateUser(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    def post(self):
        if request.get_json():
            data = request.get_json()
            api_token = data['api-token']
            firstname = data['firstname']
            lastname = data['lastname']
            email = data['email']
            usertype = data['usertype']
            userstatus = data['userstatus']
            password = data['password']

            if not api_token:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

            # check api token exists in db
            register_user = users.find_one({"api_token": api_token})

            if register_user:
                register_user_api_token = register_user['api_token']
                mongo_id = register_user['_id']
                if (register_user_api_token == api_token):
                    update_user = {}
                    update_user['updated_at'] = datetime.now()

                    if firstname:
                        update_user['firstname'] = firstname

                    if lastname:
                        update_user['lastname'] = lastname

                    if email:
                        try:
                            v = validate_email(email)  # validate and get info
                            email = v["email"]  # replace with normalized form
                            update_user['email'] = email
                        except EmailNotValidError as e:
                            # email is not valid, exception message is human-readable
                            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                                          "error": {"message": str(e)}}), 403)

                    if usertype:
                        update_user['user_type'] = usertype

                    if userstatus:
                        update_user['user_status'] = userstatus

                    if password:
                        update_user['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))

                    users.find_one_and_update({"_id": mongo_id}, {"$set": update_user})

                    return make_response(
                        jsonify({"success": "true", "status_code": 200, "payload": {}}), 200)

                else:
                    return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                                  "error": {"message": "Unauthorized"}}), 403)

            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)

if __name__ == '__main__':
    app.run(debug=True)