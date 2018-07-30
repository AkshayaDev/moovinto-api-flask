from flask import Flask, request, jsonify, make_response, render_template
from flask_restplus import Api, Resource, fields, Namespace
from flask_mail import Mail, Message
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
renters = database['renters']
houseowners = database['houseowners']

app = Flask(__name__, template_folder='templates')
# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'super-unique-secret'  # Change this!
jwt = JWTManager(app)
mail = Mail(app)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
api = Api(app, version='1.0', title='MoovInto API',
    description='A sample API for MoovInto')

api.namespaces.clear()

users_api = Namespace('user', description='User related operations')
api.add_namespace(users_api)

login_model = api.model('Login', {
    'email': fields.String(description="User Email", required=True),
    'password': fields.String(description="User Password", required=True),
})

@users_api.route('/login', endpoint='login')
class Login(Resource):
    @api.response(200, 'Success')
    @api.response(401, 'Not Authorized')
    @api.response(400, 'Validation error')
    @api.expect(login_model)
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

register_model = api.model('Register', {
    'email': fields.String(description="Email", required=True),
    'password': fields.String(description="Password", required=True),
    'confpassword': fields.String(description="Confirm Password", required=True),
})

@users_api.route('/register', endpoint='register')
class Register(Resource):
    @api.response(200, 'Success')
    @api.response(401, 'Not Authorized')
    @api.response(400, 'Validation error')
    @api.expect(register_model)
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
                            "password_reset_key": "",
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


get_user_parser = api.parser()
get_user_parser.add_argument('API-TOKEN', location='headers')

@users_api.route('/<int:user_id>')
@api.header('API-TOKEN', 'User Api Token', required=True)
@api.doc(params={'user_id': 'User ID'})
@api.expect(get_user_parser)
class User(Resource):
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


update_user_parser = api.parser()
update_user_parser.add_argument('API-TOKEN', location='headers')

@users_api.route('/update-user')
@api.doc(params={'firstname': 'Firstname', 'lastname': 'Lastname', 'email': 'Email', 'usertype': 'User Type', 'userstatus': 'User Status', 'password': 'Password'})
class UpdateUser(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    @api.expect(update_user_parser)
    def put(self):
        if request.get_json():
            data = request.get_json()
            api_token = request.headers['API-TOKEN']
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

@users_api.route('/reset-password')
@api.doc(params={'email': 'User Email'})
class ResetPassword(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    @api.response(400, 'Validation error')
    def post(self):
        if request.get_json():
            data = request.get_json()
            email = data['email']

            if not email:
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

            registered_user = users.find_one({ "email" : email })

            if registered_user:
                mongo_id = registered_user['_id']
                update_user = {}
                reset_key = create_access_token(identity=email)
                update_user['password_reset_key'] = reset_key
                users.find_one_and_update({"_id": mongo_id}, {"$set": update_user})
                msg = Message(subject="MoovInto Password Reset",
                              sender="moovinto@gmail.com",
                              recipients=[email])
                link = request.url_root + "?resetkey=" + reset_key
                msg.html = render_template('/mails/reset-password.html', link=link)
                mail.send(msg)

            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)


renters_resource = api.parser()
renters_resource.add_argument('API-TOKEN', location='headers')
@users_api.route('/update-renters-data')
@api.doc(params={'accommodation_for': 'Looking for a place for', 'accommodation_wanted_applicants': 'data{}', 'teamup': 'Share house together', 'where_to_live': 'Location', 'max_budget': 'Max budget', 'move_date': 'Move Date', 'preferred_length_of_stay': 'Length of stay', 'about_renter': 'About Renter', 'renter_description': 'Renter Description', 'roommate_preferences': 'Roommate Preferences', 'email': 'Email'})
class UpdateRentersData(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    @api.expect(renters_resource)
    def put(self):
        if request.get_json():
            api_token = request.headers['API-TOKEN']
            data = request.get_json()

            if not api_token:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

            # check api token exists in db
            register_user = users.find_one({"api_token": api_token})

            if register_user:
                newrenter = {
                    "accommodation_for": data['accommodation_for'],
                    "accommodation_wanted_applicants": data['accommodation_wanted_applicants'],
                    "teamup": data['teamup'],
                    "where_to_live": data['where_to_live'],
                    "max_budget": data['max_budget'],
                    "move_date": data['move_date'],
                    "preferred_length_of_stay": data['preferred_length_of_stay'],
                    "about_renter": data['about_renter'],
                    "renter_description": data['renter_description'],
                    "roommate_preferences": data['roommate_preferences'],
                    "email": register_user['email']
                }
                database.renters.insert_one(newrenter)
                return make_response(jsonify({"success": "true", "status_code": 200, "payload": newrenter}), 200)
            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                      "error": {"message": "Unauthorized"}}), 403)



houseowners_resource = api.parser()
houseowners_resource.add_argument('API-TOKEN', location='headers')
@users_api.route('/update-houseowners-data')
@api.doc(params={'accommodation_for': 'Looking for a place for', 'accommodation_wanted_applicants': 'data{}', 'teamup': 'Share house together', 'where_to_live': 'Location', 'max_budget': 'Max budget', 'move_date': 'Move Date', 'preferred_length_of_stay': 'Length of stay', 'about_renter': 'About Renter', 'renter_description': 'Renter Description', 'roommate_preferences': 'Roommate Preferences', 'email': 'Email'})
class UpdateHouseownersData(Resource):
    @api.response(200, 'Success')
    @api.response(403, 'Not Authorized')
    @api.expect(houseowners_resource)
    def put(self):
        if request.get_json():
            api_token = request.headers['API-TOKEN']
            data = request.get_json()

            if not api_token:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

            # check api token exists in db
            register_user = users.find_one({"api_token": api_token})

            if register_user:
                newhouseowner = {
                    "renter_preferences": data['renter_preferences'],
                    "property_id": data['property_id'],
                    "email": register_user['email']
                }
                database.renters.insert_one(newhouseowner)
                return make_response(jsonify({"success": "true", "status_code": 200, "payload": newhouseowner}), 200)
            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                      "error": {"message": "Unauthorized"}}), 403)

if __name__ == '__main__':
    app.run(debug=True)