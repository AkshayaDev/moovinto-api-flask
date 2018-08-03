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
from bson import json_util
import json
import bcrypt

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
database = client['moovintodb']
users = database['users']
renters = database['renters']
houseowners = database['houseowners']
properties = database['properties']

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

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'API-TOKEN'
    }
}

api.namespaces.clear()

users_api = Namespace('user', description='User related operations')
api.add_namespace(users_api)

status_codes_model = api.model('HTTP Status codes', {
    '200': fields.String(title="OK", description="The request was successful."),
    '201': fields.String(title="Created", description="The resource was successfully created."),
    '202': fields.String(title="Async created", description="The resource was asynchronously created"),
    '400': fields.String(title="Bad request", description="Bad request"),
    '401': fields.String(title="Unauthorized", description="Your API key is invalid"),
    '402': fields.String(title="Over quota", description="Over plan quota on this endpoint"),
    '404': fields.String(title="Not found", description="The resource does not exist"),
    '422': fields.String(title="Validation error", description="A validation error occurred"),
    '50X': fields.String(title="Internal Server Error", description="An error occurred with our API"),
})

login_model = api.model('Login', {
    'email': fields.String(description="User Email", required=True),
    'password': fields.String(description="User Password", required=True),
})

@users_api.route('/login')
class Login(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(401, 'Not Authorized')
    @users_api.response(400, 'Validation error')
    @users_api.expect(login_model, validate=True)
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

@users_api.route('/register')
class Register(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(401, 'Not Authorized')
    @users_api.response(400, 'Validation error')
    @users_api.expect(register_model, validate=True)
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
                            "phone": "",
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
get_user_parser.add_argument('API-TOKEN', location='headers', required=True)
get_user_parser.add_argument('user_id', type=int, location='args')

@users_api.route('/<int:user_id>')
@users_api.doc(security='apikey')
@users_api.expect(get_user_parser, validate=True)
class User(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
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
update_user_parser.add_argument('API-TOKEN', location='headers', required=True)

update_user_model = api.model('Update User', {
    'firstname': fields.String(description="Firstname"),
    'lastname': fields.String(description="Lastname"),
    'email': fields.String(description="Email"),
    'phone': fields.String(description="Phone"),
    'usertype': fields.String(description="User Type"),
    'userstatus': fields.String(description="User Status"),
    'password': fields.String(description="Password"),
})

@users_api.route('/update-user')
@users_api.doc(security='apikey')
@users_api.expect(update_user_parser, validate=True)
class UpdateUser(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
    @users_api.expect(update_user_model)
    def put(self):
        if request.get_json():
            data = request.get_json()
            api_token = request.headers['API-TOKEN']
            firstname = data['firstname']
            lastname = data['lastname']
            email = data['email']
            phone = data['phone']
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

                    if phone:
                        update_user['phone'] = phone

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

                    registered_user = users.find_one({"_id": mongo_id})
                    if registered_user:
                        update_user_payload = {
                            "user_id": registered_user['user_id'],
                            "username": registered_user['username'],
                            "firstname": registered_user['firstname'],
                            "lastname": registered_user['lastname'],
                            "email": registered_user['email'],
                            "phone": registered_user['phone'],
                            "user_type": registered_user['user_type']
                        }
                    else:
                        update_user_payload = {}

                    return make_response(
                        jsonify({"success": "true", "status_code": 200, "payload": update_user_payload}), 200)

                else:
                    return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                                  "error": {"message": "Unauthorized"}}), 403)

            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)


reset_pwd_model = api.model('Reset Password', {
    'email': fields.String(description="Email")
})

@users_api.route('/reset-password')
class ResetPassword(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
    @users_api.response(400, 'Validation error')
    @users_api.expect(reset_pwd_model, validate=True)
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
                return make_response(
                    jsonify({"success": "true", "status_code": 200, "payload": {}}), 200)

            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)


renters_resource = api.parser()
renters_resource.add_argument('API-TOKEN', location='headers', required=True)

roommate_preferences_model = api.model('Roommate Preferences', {
    'key': fields.String
})

update_renter_model = api.model('Update Renter', {
#    'accommodation_for': fields.String(description="Looking for a place for"),
#    'accommodation_wanted_applicants': fields.String(description="data{}"),
    'teamup': fields.String(description="Share house together"),
    'where_to_live': fields.String(description="Location"),
    'max_budget': fields.String(description="Max budget"),
    'move_date': fields.String(description="Move Date"),
    'preferred_length_of_stay': fields.String(description="Length of stay"),
    'about_renter': fields.String(description="About Renter"),
    'renter_description': fields.String(description="Renter Description"),
    'roommate_preferences': fields.List(fields.Nested(roommate_preferences_model))
})

@users_api.route('/update-renters-data')
@users_api.doc(security='apikey')
@users_api.expect(renters_resource, validate=True)
class UpdateRentersData(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
    @users_api.expect(update_renter_model)
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
                # check already exists
                check_renter = renters.find_one({"email": register_user['email']})
                if check_renter:
                    mongo_id = check_renter['_id']
                    update_renter = {
                       # "accommodation_for": data['accommodation_for'],
                       # "accommodation_wanted_applicants": data['accommodation_wanted_applicants'],
                        "teamup": data['teamup'],
                        "where_to_live": data['where_to_live'],
                        "max_budget": data['max_budget'],
                        "move_date": data['move_date'],
                        "preferred_length_of_stay": data['preferred_length_of_stay'],
                        "about_renter": data['about_renter'],
                        "renter_description": data['renter_description'],
                        "roommate_preferences": data['roommate_preferences']
                    }
                    renters.find_one_and_update({"_id": mongo_id}, {"$set": update_renter})
                    return make_response(jsonify({"success": "true", "status_code": 200, "payload": update_renter}), 200)
                else:
                    newrenter = {
                       # "accommodation_for": data['accommodation_for'],
                       # "accommodation_wanted_applicants": data['accommodation_wanted_applicants'],
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


renter_preferences_model = api.model('Renters Preferences', {
    'key': fields.String
})

update_houseowner_model = api.model('Update House Owner', {
    'about_houseowner': fields.String(description="About House Owner"),
    'houseowner_description': fields.String(description="House Owner Description"),
    'renter_preferences': fields.List(fields.Nested(renter_preferences_model)),
    'property_id': fields.Integer(description="Property ID")
})

houseowners_resource = api.parser()
houseowners_resource.add_argument('API-TOKEN', location='headers', required=True)
@users_api.route('/update-houseowners-data')
@users_api.doc(security='apikey')
class UpdateHouseownersData(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
    @users_api.expect(update_houseowner_model)
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
                    "about_houseowner": data['about_houseowner'],
                    "houseowner_description": data['houseowner_description'],
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


property_api = Namespace('property', description='Property related operations')
api.add_namespace(property_api)

property_resource = api.parser()
property_resource.add_argument('API-TOKEN', location='headers', required=True)

room_images_model = api.model('Images', {
    'url': fields.String
})

room_details_model = api.model('Room Details', {
    'room_id': fields.String(description="Room ID"),
    'description': fields.String(description="Description"),
    'facilities': fields.String(description="Room facilities"),
    'images': fields.List(fields.Nested(room_images_model))
})

add_property_model = api.model('Add Property', {
    'name': fields.String(description="Name"),
    'status': fields.String(description="Status"),
    'address': fields.String(description="Address"),
    'country_code': fields.String(description="Country Code"),
    'state_county_code': fields.String(description="State Code"),
    'city': fields.String(description="City"),
    'zip_code': fields.Integer(description="Zip Code"),
    'lat': fields.String(description="Latitude"),
    'lng': fields.String(description="Longitude"),
    'typeofproperty': fields.String(description="Type of property"),
    'number_of_flatmates': fields.String(description="Number of flatmates"),
    'internet_access': fields.String(description="Internet access"),
    'parking': fields.String(description="Parking"),
    'room_details': fields.List(fields.Nested(room_details_model)),
    'description': fields.String(description="Description"),
})

@property_api.route('/add')
@property_api.doc(security='apikey')
@property_api.expect(property_resource, validate=True)
class UpdateRentersData(Resource):
    @property_api.response(200, 'Success')
    @property_api.response(403, 'Not Authorized')
    @property_api.expect(add_property_model)
    def post(self):
        if request.get_json():
            api_token = request.headers['API-TOKEN']
            data = request.get_json()

            if not api_token:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

            # check api token exists in db
            register_user = users.find_one({"api_token": api_token})

            if register_user:
                new_property_id = database.properties.count() + 1
                newproperty = {
                    "name": data['name'],
                    "property_id": new_property_id,
                    "email": register_user['email'],
                    "status": data['status'],
                    "address": data['address'],
                    "country_code": data['country_code'],
                    "state_county_code": data['state_county_code'],
                    "city": data['city'],
                    "zip_code": data['zip_code'],
                    "lat": data['lat'],
                    "lng": data['lng'],
                    "typeofproperty": data['typeofproperty'],
                    "number_of_flatmates": data['number_of_flatmates'],
                    "internet_access": data['internet_access'],
                    "parking": data['parking'],
                    "description": data['description'],
                    "room_details": data['room_details']
                }
                database.properties.insert_one(newproperty)
                # print(dumps(newproperty))
                return make_response(jsonify({"success": "true", "status_code": 200, "payload": json.loads(json_util.dumps(newproperty))}), 200)
            else:
                return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                              "error": {"message": "Unauthorized"}}), 403)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                      "error": {"message": "Unauthorized"}}), 403)


get_property_parser = api.parser()
get_property_parser.add_argument('API-TOKEN', location='headers', required=True)
get_property_parser.add_argument('country_code', type=str, location='args', required=False)
get_property_parser.add_argument('state_county_code', type=str, location='args', required=False)
get_property_parser.add_argument('zip_code', type=int, location='args', required=False)
@property_api.route('/location')
@property_api.doc(security='apikey')
@property_api.expect(get_property_parser, validate=True)
class PropertyLocation(Resource):
    @property_api.response(200, 'Success')
    @property_api.response(403, 'Not Authorized')
    @property_api.response(404, 'Not Found')
    def get(self):
        # check Api token exists
        api_token = request.headers['API-TOKEN']
        country_code = request.args.get("country_code")
        state_county_code = request.args.get("state_county_code")
        zip_code = request.args.get("zip_code")
        if not api_token:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                          "error": {"message": "Unauthorized"}}), 403)

        # check api token exists in db
        register_user = users.find_one({"api_token": api_token})

        if register_user:
            location_search_data = {}

            if country_code:
                location_search_data['country_code'] = country_code

            if state_county_code:
                location_search_data['state_county_code'] = state_county_code

            if zip_code:
                location_search_data['zip_code'] = zip_code


            # find property with provided data
            location_data = properties.find(location_search_data)

            if location_data:
                return make_response(jsonify(
                    {"success": "true", "status_code": 200, "payload": json.loads(json_util.dumps(location_data))}), 200)

            else:
                return make_response(jsonify({"success": "false", "status_code": 404, "payload": {},
                                              "error": {"message": "Not found"}}), 404)

        else:
            return make_response(jsonify({"success": "false", "status_code": 403, "payload": {},
                                      "error": {"message": "Unauthorized"}}), 403)



if __name__ == '__main__':
    app.run(debug=True)