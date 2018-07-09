from flask import Flask
from flask_restplus import Api, Resource, fields
from pymongo import MongoClient

client = MongoClient()
db = client.moovinto_db # Database
users = db.users # Collection or table
# db.users.create_index('email', unique=True)
# db.users.create_index('api_token', unique=True)
singleuser = {
    'username':'akii',
    'firstname':'akshaya',
    'lastname':'Swaroop',
    'email': 'akshaynsp@gmail.com',
    'password': 'ak112345',
    'api_token': '',
    'user_type': '',
    'user_status': '',
    'user_activation_key': '',
    'remember_token': '',
    'created_at': '',
    'updated_at': ''
}
#users.insert_one(singleuser)

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
api = Api(app, version='1.0', title='MoovInto API',
    description='A sample API for MoovInto',
)

@api.route('/login', endpoint='login')
@api.doc(params={'username': 'Username','password': 'Password'})
class Login(Resource):
    def post(self, id):
        return {}
    
@api.route('/register', endpoint='register')
@api.doc(params={'username': 'Username','password': 'Password','confpassword': 'Confirm Password'})
class Register(Resource):
    def post(self, id):
        return {}

@api.route('/user/<api_token>', endpoint='user')
@api.doc(params={'api_token': 'Api Token'})
class User(Resource):
    def get(self, api_token):
        return {}

if __name__ == '__main__':
    app.run(debug=True)