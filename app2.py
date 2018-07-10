from flask import Flask, request
from flask_restplus import Api, Resource, fields
import pymongo

uri = "mongodb://127.0.0.1:27017"
client = pymongo.MongoClient(uri)
database = client['restapi']
users = database['users']

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

#database.users.insert_one(singleuser)

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True
api = Api(app, version='1.0', title='MoovInto API',
    description='A sample API for MoovInto')


@api.route('/login', endpoint='login')
@api.doc(params={'username': 'Username','password': 'Password'})
class Login(Resource):
    @api.doc(responses={403: 'Not Authorized'})
    def post(self):
        if request.method == 'POST':
            requestedusername = request.form['username']
            requestedpassword = request.form['password']
            return { 'data': requestedusername}, 201
        else:
            api.abort(403)


if __name__ == '__main__':
    app.run(debug=True)
