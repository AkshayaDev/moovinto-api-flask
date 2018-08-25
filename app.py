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
import pycountry
import string
from random import *
import us_states_cities
import api_responses

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

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'moovinto.help@gmail.com'
app.config['MAIL_PASSWORD'] = 'moovinto123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
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

general_apis = Namespace('general', description='General Endpoints')
api.add_namespace(general_apis)

users_api = Namespace('user', description='User related operations')
api.add_namespace(users_api)


@general_apis.route('/welcome-screen/data')
class WelcomeScreenData(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = {
            "1": dict(title="Welcome In", description="Find a home, match a flatmate, schedule a viewing and sign a lease."),
            "2": dict(title="Set Home Criteria", description="Setup your home preferences. Number of rooms, appliances, house rules and more."),
            "3": dict(title="Find Flatmates", description="With smart indicators, setup filters and priorities your criteria for the perfect flatmate.")
        }
        return api_responses.success_response(response_payload)

@general_apis.route('/welcome-screen/<int:screen_id>')
class WelcomeScreen(Resource):
    @general_apis.response(200, 'Success')
    def get(self, screen_id):

        if (screen_id==1):
            response_payload = dict(screen_id=1, title="Welcome In", description="Find a home, match a flatmate, schedule a viewing and sign a lease.")

        elif (screen_id==2):
            response_payload = dict(screen_id=2, title="Set Home Criteria", description="Setup your home preferences. Number of rooms, appliances, house rules and more.")

        elif (screen_id==3):
            response_payload = dict(screen_id=3, title="Find Flatmates", description="With smart indicators, setup filters and priorities your criteria for the perfect flatmate.")

        else:
            return api_responses.error_response("MOOV_ERR_11", api_responses.moovinto_error_codes["MOOV_ERR_11"])

        return api_responses.success_response(response_payload)


@general_apis.route('/list-countries')
class ListCountries(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        # country code list
        countries = {}
        for country in pycountry.countries:
            countries[country.alpha_2] = country.name

        response_payload = {
            "countries": countries
        }
        return api_responses.success_response(response_payload)


@general_apis.route('/us/states')
class UsStates(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = {
            "states": us_states_cities.get_us_states(),
        }
        return api_responses.success_response(response_payload)


@general_apis.route('/us-cities/<state_code>')
class UsStatesCities(Resource):
    @general_apis.response(200, 'Success')
    def get(self, state_code):
        statecode = state_code.upper()
        response_payload = {
           "cities": us_states_cities.get_us_city_by_state(statecode)
        }
        return api_responses.success_response(response_payload)


@general_apis.route('/current-active-cities')
class CurrentActiveCities(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = dict(cities=list(('Boston', 'Houstan', 'Los Angeles', 'New York City', 'San Francisco', 'Seattle', 'Washington D.C')))
        return api_responses.success_response(response_payload)


@general_apis.route('/occupations')
class OccupationsData(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = dict(occupations=list(('accountant','actor','actress','air traffic controller','architect','artist','attorney','banker','bartender','barber','bookkeeper','builder','businessman','businesswoman','businessperson','butcher','carpenter','cashier','chef','coach','dental hygienist','dentist','designer','developer','dietician','doctor','economist','editor','electrician','engineer','farmer','filmmaker','fisherman','flight attendant','jeweler','judge','lawyer','mechanic','musician','nutritionist','nurse','optician','painter','pharmacist','photographer','physician','physicians assistant','pilot','plumber','police officer','politician','professor','programmer','psychologist','receptionist','salesman','salesperson','saleswoman','secretary','singer','surgeon','teacher','therapist','translator','translator','undertaker','veterinarian','videographer','waiter','waitress','writer')))
        return api_responses.success_response(response_payload)


@general_apis.route('/universities')
class UniversitiesData(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = dict(universities=list(('Allen University', 'Baker University')))
        return api_responses.success_response(response_payload)


@general_apis.route('/majors')
class MajorsData(Resource):
    @general_apis.response(200, 'Success')
    def get(self):
        response_payload = dict(majors=list(('Athletic Training','Biology','Chemistry','Environmental Science','Exercise Sci/Kinesiology','Fisheries and Wildlife','Food Science','Forest Management','Marine Science','Nursing (RN/BSN)','Organic/Urban Farming','Pharmacy','Physicians Assistant','Pre - Dental','Pre - Medical','Pre - Veterinary Medicine','Apparel/Textile Design','Architecture','Dance','Film/Broadcast','Fine/Studio Art','Graphic Design','Industrial Design','Interior Design','Landscape Architecture','Music','Theatre','Urban Planning','Video Game Design','Web Design/Digital Media','Arts Management','Education','Emergency Management','English/Writing','Equine Science/Mgmt','Family & Child Science','History','Journalism','Language Studies','Non-Profit Management','Peace/Conflict Studies','Philosophy','Political Science','Social Science','Sports Turf/Golf Mgmt','Women/Gender Studies','Aerospace Engineering','Astronomy','Aviation/Aeronautics','Biomedical Engineering','Chemical Engineering','Civil Engineering','Computer Science','Electrical Engineering','Energy Science','Engineering','Imaging Science','Industrial Engineering','Industrial Technology','Materials Science','Mathematics','Mechanical Engineering','Accounting - General','Business - General','Construction Management','Finance & Economics','Hospitality Management','Human Resources Mgmt','Information Systems (MIS)','Insurance & Risk Mgmt','National Parks Management','Public Health Administration','Sport Management','Supply Chain Mgmt (Logistics)')))
        return api_responses.success_response(response_payload)

# Property amenities details model
amenity_details_model = api.model('Amenity details',{
    'parking': fields.Boolean(description="Parking"),
    'internet_access': fields.Boolean(description="Internet Access"),
    'balcony': fields.Boolean(description="Balcony"),
    'air_conditioning': fields.Boolean(description="Air Conditioning"),
})

# Property rules model
property_rules_model = api.model('Property Rules',{
    'smoking_allowed': fields.Boolean(description="Smoking Allowed"),
    'pets_allowed': fields.Boolean(description="Pets Allowed"),
    'couples_allowed': fields.Boolean(description="Couples Allowed"),
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
    @users_api.response(404, 'Not found')
    @users_api.response(406, 'Not Acceptable')
    @users_api.expect(login_model, validate=True)
    def post(self):
        if request.get_json():
            data = request.get_json()
            email = data['email']
            password = data['password']

            if not email:
                return api_responses.error_response("MOOV_ERR_08", api_responses.moovinto_error_codes["MOOV_ERR_08"])

            if not password:
                return api_responses.error_response("MOOV_ERR_08", api_responses.moovinto_error_codes["MOOV_ERR_08"])

            if email:
                try:
                    v = validate_email(email)  # validate and get info
                    email = v["email"]  # replace with normalized form
                except EmailNotValidError as e:
                    # email is not valid, exception message is human-readable
                    return api_responses.error_response("MOOV_ERR_05", str(e))
                    # return make_response(jsonify({"success": "false", "status_code": 400, "payload": {}, "error": {"message": str(e)}}), 400)

            login_user = users.find_one({ "email" : email })

            if login_user:
                hashedpw = login_user['password']
                mongo_id = login_user['_id']
                if bcrypt.checkpw(password.encode('utf-8'), hashedpw):
                    # Identity can be any data that is json serializable
                    access_token = create_access_token(identity = login_user['email'])
                    users.find_one_and_update({"_id": mongo_id},{"$set": {"api_token": access_token}})
                    user_dict = {
                        "user_id": login_user['user_id'],
                        "email": login_user['email'],
                        "firstname": login_user['firstname'],
                        "lastname": login_user['lastname'],
                        "user_type": login_user['user_type'],
                        "user_status": login_user['user_status'],
                    }
                    login_payload = {
                        "api_token": access_token,
                        "user": user_dict
                    }
                    return api_responses.success_response(login_payload)
                else:
                    return api_responses.error_response("MOOV_ERR_09", api_responses.moovinto_error_codes["MOOV_ERR_09"])

            else:
                return api_responses.error_response("MOOV_ERR_11", "User not found")
        else:
            return api_responses.error_response("MOOV_ERR_01", api_responses.moovinto_error_codes["MOOV_ERR_01"])

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
    @users_api.response(406, 'Not Acceptable')
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
                    return api_responses.error_response("MOOV_ERR_05", str(e))

            if all([email, password, confpassword]):
                if password == confpassword:
                    register_user = users.find_one({"email": email})
                    if register_user:
                        return api_responses.error_response("MOOV_ERR_06", api_responses.moovinto_error_codes["MOOV_ERR_06"])
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
                        user_dict = {
                            "user_id": new_user_id,
                            "email": email,
                            "firstname": "",
                            "lastname": "",
                            "user_type": "",
                            "user_status": "",
                        }
                        register_payload = {
                            "api_token": api_token,
                            "user": user_dict
                        }
                        return api_responses.success_response(register_payload)

                else:
                    return api_responses.error_response("MOOV_ERR_07", api_responses.moovinto_error_codes["MOOV_ERR_07"])

            else:
                return api_responses.error_response("MOOV_ERR_08", api_responses.moovinto_error_codes["MOOV_ERR_08"])

        else:
            return api_responses.error_response("MOOV_ERR_01", api_responses.moovinto_error_codes["MOOV_ERR_01"])


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
            return api_responses.error_response("MOOV_ERR_03", api_responses.moovinto_error_codes["MOOV_ERR_03"])

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
                return api_responses.success_response(user_payload)
            else:
                return api_responses.error_response("MOOV_ERR_10", api_responses.moovinto_error_codes["MOOV_ERR_10"])

        else:
            return api_responses.error_response("MOOV_ERR_11", "User not found")


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
                return api_responses.error_response("MOOV_ERR_03", api_responses.moovinto_error_codes["MOOV_ERR_03"])

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
                            return api_responses.error_response("MOOV_ERR_05", str(e))

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

                    return api_responses.success_response(update_user_payload)

                else:
                    return api_responses.error_response("MOOV_ERR_04", api_responses.moovinto_error_codes["MOOV_ERR_04"])

            else:
                return api_responses.error_response("MOOV_ERR_11", "User not found")

        else:
            return api_responses.error_response("MOOV_ERR_01", api_responses.moovinto_error_codes["MOOV_ERR_01"])


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
                return api_responses.error_response("MOOV_ERR_08", api_responses.moovinto_error_codes["MOOV_ERR_08"])

            if email:
                try:
                    v = validate_email(email)  # validate and get info
                    email = v["email"]  # replace with normalized form
                except EmailNotValidError as e:
                    # email is not valid, exception message is human-readable
                    return api_responses.error_response("MOOV_ERR_05", str(e))

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
                link = request.url_root + "reset-password-verify/?resetkey=" + reset_key + "&email=" + email
                msg.html = render_template('/mails/reset-password.html', link=link)
                mail.send(msg)
                mailsentpayload = {}
                return api_responses.success_response(mailsentpayload)

            else:
                return api_responses.error_response("MOOV_ERR_11", "User not found")


reset_password_verify_parser = api.parser()
reset_password_verify_parser.add_argument('resetkey', type=str, location='args', required=True)
reset_password_verify_parser.add_argument('email', type=str, location='args', required=True)

@users_api.route('/reset-password-verify')
@users_api.expect(reset_password_verify_parser, validate=True)
class ResetPasswordVerify(Resource):
    @users_api.response(200, 'Success')
    @users_api.response(403, 'Not Authorized')
    def get(self):
        resetkey = request.args.get("resetkey")
        email = request.args.get("email")
        if not resetkey:
            return api_responses.error_response("MOOV_ERR_08", api_responses.moovinto_error_codes["MOOV_ERR_08"])

        registered_user = users.find_one({"email": email})

        if registered_user:
            mongo_id = registered_user['_id']
            pwd_reset_key_db = registered_user['password_reset_key']
            if (pwd_reset_key_db==resetkey):
                update_user = {}
                min_char = 8
                max_char = 12
                allchar = string.ascii_letters + string.digits
                password = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
                update_user['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
                update_user['password_reset_key'] = ""
                users.find_one_and_update({"_id": mongo_id}, {"$set": update_user})
                msg = Message(subject="MoovInto New Password",
                              sender="moovinto@gmail.com",
                              recipients=[email])
                msg.html = render_template('/mails/random-password.html', pwd=password)
                mail.send(msg)
                mailsentpayload = {}
                return api_responses.success_response(mailsentpayload)

            else:
                return api_responses.error_response("MOOV_ERR_10", api_responses.moovinto_error_codes["MOOV_ERR_10"])
        else:
            return api_responses.error_response("MOOV_ERR_11", "User not found")

renters_resource = api.parser()
renters_resource.add_argument('API-TOKEN', location='headers', required=True)

roommate_preferences_model = api.model('Roommate Preferences', {
    'looking_for': fields.List(fields.String(example="student")),
    'behaviours': fields.List(fields.String(example="Smoking")),
    'cleaning_habits': fields.List(fields.String),
})

property_preferences_model = api.model('Property Preferences', {
    'property_type': fields.List(fields.String),
    'no_of_bedrooms': fields.List(fields.Integer),
    'no_of_bathrooms': fields.List(fields.Integer),
    'amenities_required': fields.List(fields.String(example="Wifi")),
    'property_rules': fields.List(fields.String(example="Smoking Allowed")),
})

location_model = api.model('Location', {
    'country_code': fields.String(description="Country code"),
    'state_county_code': fields.String(description="State/County code"),
    'city': fields.String(description="City")
})

update_renter_model = api.model('Update Renter', {
    'teamup': fields.Boolean(description="Share house together"),
    'where_to_live': fields.Nested(location_model),
    'max_budget': fields.String(description="Max budget"),
    'move_date': fields.String(description="Move Date"),
    'preferred_length_of_stay': fields.String(description="Length of stay"),
    'about_renter': fields.String(description="About Renter"),
    'renter_description': fields.String(description="Renter Description"),
    'behaviours': fields.List(fields.String(example="Smoking")),
    'cleaning_habits': fields.List(fields.String),
    'profession': fields.String(description="Student"),
    'roommate_preferences': fields.List(fields.Nested(roommate_preferences_model)),
    'property_preferences': fields.Nested(property_preferences_model)
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
                return api_responses.error_response("MOOV_ERR_03", api_responses.moovinto_error_codes["MOOV_ERR_03"])

            # check api token exists in db
            register_user = users.find_one({"api_token": api_token})

            if register_user:
                # check already exists
                check_renter = renters.find_one({"email": register_user['email']})
                if check_renter:
                    mongo_id = check_renter['_id']
                    update_renter = {
                        "teamup": data['teamup'],
                        "where_to_live": data['where_to_live'],
                        "max_budget": data['max_budget'],
                        "move_date": data['move_date'],
                        "preferred_length_of_stay": data['preferred_length_of_stay'],
                        "about_renter": data['about_renter'],
                        "renter_description": data['renter_description'],
                        "behaviours": data['behaviours'],
                        "cleaning_habits": data['cleaning_habits'],
                        "profession": data['profession'],
                        "roommate_preferences": data['roommate_preferences'],
                        "property_preferences": data['property_preferences'],
                        "email": check_renter['email']
                    }
                    renters.find_one_and_update({"_id": mongo_id}, {"$set": update_renter})
                    return api_responses.success_response(update_renter)
                else:
                    newrenter = {
                        "teamup": data['teamup'],
                        "where_to_live": data['where_to_live'],
                        "max_budget": data['max_budget'],
                        "move_date": data['move_date'],
                        "preferred_length_of_stay": data['preferred_length_of_stay'],
                        "about_renter": data['about_renter'],
                        "renter_description": data['renter_description'],
                        "behaviours": data['behaviours'],
                        "cleaning_habits": data['cleaning_habits'],
                        "profession": data['profession'],
                        "roommate_preferences": data['roommate_preferences'],
                        "property_preferences": data['property_preferences'],
                        "email": register_user['email']
                    }
                    database.renters.insert_one(newrenter)
                    return api_responses.success_response(newrenter)

            else:
                return api_responses.error_response("MOOV_ERR_10", api_responses.moovinto_error_codes["MOOV_ERR_10"])

        else:
            return api_responses.error_response("MOOV_ERR_01", api_responses.moovinto_error_codes["MOOV_ERR_01"])

"""
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
@users_api.expect(houseowners_resource, validate=True)
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

"""

property_api = Namespace('property', description='Property related operations')
api.add_namespace(property_api)

property_resource = api.parser()
property_resource.add_argument('API-TOKEN', location='headers', required=True)

room_details_model = api.model('Room Details', {
    'room_id': fields.Integer(description="Room ID"),
    'description': fields.String(description="Description"),
    'facilities': fields.List(fields.String),
    'images': fields.List(fields.Url),
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
    'price': fields.Integer(description="Price"),
    'number_of_flatmates': fields.String(description="Number of flatmates"),
    'amenities': fields.List(fields.Nested(amenity_details_model)),
    'property_rules': fields.List(fields.Nested(property_rules_model)),
    'total_bedrooms': fields.Integer(description="Total Bedrooms"),
    'total_bathrooms': fields.Integer(description="Total Bathrooms"),
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
                    "price": data['price'],
                    "address": data['address'],
                    "country_code": data['country_code'],
                    "state_county_code": data['state_county_code'],
                    "city": data['city'],
                    "zip_code": data['zip_code'],
                    "lat": data['lat'],
                    "lng": data['lng'],
                    "typeofproperty": data['typeofproperty'],
                    "total_bedrooms": data['total_bedrooms'],
                    "total_bathrooms": data['total_bathrooms'],
                    "number_of_flatmates": data['number_of_flatmates'],
                    "amenities": data['amenities'],
                    "property_rules": data['property_rules'],
                    "description": data['description'],
                    "room_details": data['room_details']
                }
                database.properties.insert_one(newproperty)
                # print(dumps(newproperty))
                return api_responses.success_response(newproperty)
                # return make_response(jsonify({"success": "true", "status_code": 200, "payload": json.loads(json_util.dumps(newproperty))}), 200)
            else:
                return api_responses.error_response("MOOV_ERR_10", api_responses.moovinto_error_codes["MOOV_ERR_10"])

        else:
            return api_responses.error_response("MOOV_ERR_01", api_responses.moovinto_error_codes["MOOV_ERR_01"])


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
            return api_responses.error_response("MOOV_ERR_03", api_responses.moovinto_error_codes["MOOV_ERR_03"])

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
                return api_responses.error_response("MOOV_ERR_10", api_responses.moovinto_error_codes["MOOV_ERR_10"])

        else:
            return api_responses.error_response("MOOV_ERR_11", api_responses.moovinto_error_codes["MOOV_ERR_11"])


search_api = Namespace('find', description='Search operations')
api.add_namespace(search_api)

search_resource = api.parser()
search_resource.add_argument('API-TOKEN', location='headers', required=True)

@search_api.route('/flatmates')
@search_api.doc(security='apikey')
@search_api.expect(search_resource, validate=True)
class FindFlatmates(Resource):
    @search_api.response(200, 'Success')
    @search_api.response(403, 'Not Authorized')
    @search_api.response(404, 'Not Found')
    def post(self):
        pass

@search_api.route('/renters')
@search_api.doc(security='apikey')
@search_api.expect(search_resource, validate=True)
class FindRenters(Resource):
    @search_api.response(200, 'Success')
    @search_api.response(403, 'Not Authorized')
    @search_api.response(404, 'Not Found')
    def post(self):
        pass


if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000')
