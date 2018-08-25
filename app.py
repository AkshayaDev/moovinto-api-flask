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
        response_payload = dict(universities=list(('Abilene Christian University (TX)','Abraham Baldwin Agricultural College (GA)','Academy of Art University (CA)','Acadia University (None)','Adams State University (CO)','Adelphi University (NY)','Adrian College (MI)','Adventist University of Health Sciences (FL)','Agnes Scott College (GA)','Alabama Agricultural and Mechanical University (AL)','Alabama State University (AL)','Alaska Pacific University (AK)','Albany College of Pharmacy and Health Sciences (NY)','Albany State University (GA)','Albertus Magnus College (CT)','Albion College (MI)','Albright College (PA)','Alcorn State University (MS)','Alderson Broaddus University (WV)','Alfred University (NY)','Alice Lloyd College (KY)','Allegheny College (PA)','Allen College (IA)','Allen University (SC)','Alliant International University (CA)','Alma College (MI)','Alvernia University (PA)','Alverno College (WI)','Amberton University (TX)','American Academy of Art (IL)','American Indian College (AZ)','American InterContinental University (IL)','American International College (MA)','American Jewish University (CA)','American Public University System (WV)','American University (DC)','American University in Bulgaria (None)','American University in Cairo (None)','American University of Beirut (None)','American University of Paris (None)','American University of Puerto Rico (PR)','Amherst College (MA)','Amridge University (AL)','Anderson University (IN)','Anderson University (SC)','Andrews University (MI)','Angelo State University (TX)','Anna Maria College (MA)','Antioch University (OH)','Appalachian Bible College (WV)','Appalachian State University (NC)','Aquinas College (MI)','Aquinas College (TN)','Arcadia University (PA)','Argosy University (CA)','Arizona Christian University (AZ)','Arizona State University--Tempe (AZ)','Arizona State University--West (AZ)','Arkansas Baptist College (AR)','Arkansas State University (AR)','Arkansas Tech University (AR)','Armstrong State University (GA)','Art Academy of Cincinnati (OH)','Art Center College of Design (CA)','Art Institute of Atlanta (GA)','Art Institute of Colorado (CO)','Art Institute of Houston (TX)','Art Institute of Pittsburgh (PA)','Art Institute of Portland (OR)','Art Institute of Seattle (WA)','Asbury University (KY)','Ashford University (CA)','Ashland University (OH)','Assumption College (MA)','Athens State University (AL)','Atlanta Metropolitan State College (GA)','Auburn University (AL)','Auburn University--Montgomery (AL)','Augsburg College (MN)','Augusta University (GA)','Augustana College (IL)','Augustana University (SD)','Aurora University (IL)','Austin College (TX)','Austin Peay State University (TN)','Ave Maria University (FL)','Averett University (VA)','Avila University (MO)','Azusa Pacific University (CA)','B','Babson College (MA)','Bacone College (OK)','Baker College of Flint (MI)','Baker University (KS)','Baldwin Wallace University (OH)','Ball State University (IN)','Baptist Bible College (MO)','Baptist College of Florida (FL)','Baptist Memorial College of Health Sciences (TN)','Baptist Missionary Association Theological Seminary (TX)','Bard College (NY)','Bard College at Simon\'s Rock (MA)','Barnard College (NY)','Barry University (FL)','Barton College (NC)','Bastyr University (WA)','Bates College (ME)','Bauder College (GA)','Bay Path University (MA)','Bay State College (MA)','Bayamon Central University (PR)','Baylor University (TX)','Beacon College (FL)','Becker College (MA)','Belhaven University (MS)','Bellarmine University (KY)','Bellevue College (WA)','Bellevue University (NE)','Bellin College (WI)','Belmont Abbey College (NC)','Belmont University (TN)','Beloit College (WI)','Bemidji State University (MN)','Benedict College (SC)','Benedictine College (KS)','Benedictine University (IL)','Benjamin Franklin Institute of Technology (MA)','Bennett College (NC)','Bennington College (VT)','Bentley University (MA)','Berea College (KY)','Berkeley College (NJ)','Berkeley College (NY)','Berklee College of Music (MA)','Berry College (GA)','Bethany College (KS)','Bethany College (WV)','Bethany Lutheran College (MN)','Bethel College (IN)','Bethel College (KS)','Bethel University (TN)','Bethel University (MN)','Bethune-Cookman University (FL)','BI Norwegian Business School (None)','Binghamton University--SUNY (NY)','Biola University (CA)','Birmingham-Southern College (AL)','Bismarck State College (ND)','Black Hills State University (SD)','Blackburn College (IL)','Blessing-Rieman College of Nursing and Health Sciences (IL)','Bloomfield College (NJ)','Bloomsburg University of Pennsylvania (PA)','Blue Mountain College (MS)','Bluefield College (VA)','Bluefield State College (WV)','Bluffton University (OH)','Boise State University (ID)','Boricua College (NY)','Boston Architectural College (MA)','Boston College (MA)','Boston Conservatory (MA)','Boston University (MA)','Bowdoin College (ME)','Bowie State University (MD)','Bowling Green State University (OH)','Bradley University (IL)','Brandeis University (MA)','Brandman University (CA)','Brazosport College (TX)','Brenau University (GA)','Brescia University (KY)','Brevard College (NC)','Brewton-Parker College (GA)','Briar Cliff University (IA)','Briarcliffe College (NY)','Bridgewater College (VA)','Bridgewater State University (MA)','Brigham Young University--Hawaii (HI)','Brigham Young University--Idaho (ID)','Brigham Young University--Provo (UT)','Brock University (None)','Broward College (FL)','Brown University (RI)','Bryan College (TN)','Bryant University (RI)','Bryn Athyn College of the New Church (PA)','Bryn Mawr College (PA)','Bucknell University (PA)','Buena Vista University (IA)','Burlington College (VT)','Butler University (IN)','C','Cabarrus College of Health Sciences (NC)','Cabrini University (PA)','Cairn University (PA)','Caldwell University (NJ)','California Baptist University (CA)','California College of the Arts (CA)','California Institute of Integral Studies (CA)','California Institute of Technology (CA)','California Institute of the Arts (CA)','California Lutheran University (CA)','California Maritime Academy (CA)','California Polytechnic State University--San Luis Obispo (CA)','California State Polytechnic University--Pomona (CA)','California State University--Bakersfield (CA)','California State University--Channel Islands (CA)','California State University--Chico (CA)','California State University--Dominguez Hills (CA)','California State University--East Bay (CA)','California State University--Fresno (CA)','California State University--Fullerton (CA)','California State University--Long Beach (CA)','California State University--Los Angeles (CA)','California State University--Monterey Bay (CA)','California State University--Northridge (CA)','California State University--Sacramento (CA)','California State University--San Bernardino (CA)','California State University--San Marcos (CA)','California State University--Stanislaus (CA)','California University of Pennsylvania (PA)','Calumet College of St. Joseph (IN)','Calvary Bible College and Theological Seminary (MO)','Calvin College (MI)','Cambridge College (MA)','Cameron University (OK)','Campbell University (NC)','Campbellsville University (KY)','Canisius College (NY)','Capella University (MN)','Capital University (OH)','Capitol Technology University (MD)','Cardinal Stritch University (WI)','Caribbean University (PR)','Carleton College (MN)','Carleton University (None)','Carlos Albizu University (PR)','Carlow University (PA)','Carnegie Mellon University (PA)','Carroll College (MT)','Carroll University (WI)','Carson-Newman University (TN)','Carthage College (WI)','Case Western Reserve University (OH)','Castleton State College (VT)','Catawba College (NC)','Cazenovia College (NY)','Cedar Crest College (PA)','Cedarville University (OH)','Centenary College (NJ)','Centenary College of Louisiana (LA)','Central Baptist College (AR)','Central Christian College (KS)','Central College (IA)','Central Connecticut State University (CT)','Central Methodist University (MO)','Central Michigan University (MI)','Central Penn College (PA)','Central State University (OH)','Central Washington University (WA)','Centralia College (WA)','Centre College (KY)','Chadron State College (NE)','Chamberlain College of Nursing (IL)','Chaminade University of Honolulu (HI)','Champlain College (VT)','Chapman University (CA)','Charles R. Drew University of Medicine and Science (CA)','Charleston Southern University (SC)','Charter Oak State College (CT)','Chatham University (PA)','Chestnut Hill College (PA)','Cheyney University of Pennsylvania (PA)','Chicago State University (IL)','Chipola College (FL)','Chowan University (NC)','Christian Brothers University (TN)','Christopher Newport University (VA)','Cincinnati Christian University (OH)','Cincinnati College of Mortuary Science (OH)','City University of Seattle (WA)','Claflin University (SC)','Claremont McKenna College (CA)','Clarion University of Pennsylvania (PA)','Clark Atlanta University (GA)','Clark University (MA)','Clarke University (IA)','Clarkson College (NE)','Clarkson University (NY)','Clayton State University (GA)','Clear Creek Baptist Bible College (KY)','Cleary University (MI)','Clemson University (SC)','Cleveland Chiropractic College (KS)','Cleveland Institute of Art (OH)','Cleveland Institute of Music (OH)','Cleveland State University (OH)','Coastal Carolina University (SC)','Coe College (IA)','Cogswell Polytechnical College (CA)','Coker College (SC)','Colby College (ME)','Colby-Sawyer College (NH)','Colgate University (NY)','College at Brockport--SUNY (NY)','College for Creative Studies (MI)','College of Central Florida (FL)','College of Charleston (SC)','College of Coastal Georgia (GA)','College of Idaho (ID)','College of Mount St. Vincent (NY)','College of New Jersey (NJ)','College of New Rochelle (NY)','College of Our Lady of the Elms (MA)','College of Saint Rose (NY)','College of Southern Nevada (NV)','College of St. Benedict (MN)','College of St. Elizabeth (NJ)','College of St. Joseph (VT)','College of St. Mary (NE)','College of St. Scholastica (MN)','College of the Atlantic (ME)','College of the Holy Cross (MA)','College of the Ozarks (MO)','College of William & Mary (VA)','College of Wooster (OH)','Colorado Christian University (CO)','Colorado College (CO)','Colorado Mesa University (CO)','Colorado Mountain College (CO)','Colorado School of Mines (CO)','Colorado State University (CO)','Colorado State University--Pueblo (CO)','Colorado Technical University (CO)','Columbia Basin College (WA)','Columbia College (MO)','Columbia College (SC)','Columbia College Chicago (IL)','Columbia College of Nursing (WI)','Columbia International University (SC)','Columbia University (NY)','Columbus College of Art and Design (OH)','Columbus State University (GA)','Conception Seminary College (MO)','Concord University (WV)','Concordia College (AL)','Concordia College (NY)','Concordia College--Moorhead (MN)','Concordia University (NE)','Concordia University (CA)','Concordia University (OR)','Concordia University (None)','Concordia University Chicago (IL)','Concordia University Texas (TX)','Concordia University Wisconsin (WI)','Concordia University--St. Paul (MN)','Connecticut College (CT)','Converse College (SC)','Cooper Union (NY)','Coppin State University (MD)','Corban University (OR)','Cornell College (IA)','Cornell University (NY)','Cornerstone University (MI)','Cornish College of the Arts (WA)','Cottey College (MO)','Covenant College (GA)','Cox College (MO)','Creighton University (NE)','Criswell College (TX)','Crowley\'s Ridge College (AR)','Crown College (MN)','Culinary Institute of America (NY)','Culver-Stockton College (MO)','Cumberland University (TN)','CUNY--Baruch College (NY)','CUNY--Brooklyn College (NY)','CUNY--City College (NY)','CUNY--College of Staten Island (NY)','CUNY--Hunter College (NY)','CUNY--John Jay College of Criminal Justice (NY)','CUNY--Lehman College (NY)','CUNY--Medgar Evers College (NY)','CUNY--New York City College of Technology (NY)','CUNY--Queens College (NY)','CUNY--York College (NY)','Curry College (MA)','Curtis Institute of Music (PA)','D','D\'Youville College (NY)','Daemen College (NY)','Dakota State University (SD)','Dakota Wesleyan University (SD)','Dalhousie University (None)','Dallas Baptist University (TX)','Dalton State College (GA)','Daniel Webster College (NH)','Dartmouth College (NH)','Darton State College (GA)','Davenport University (MI)','Davidson College (NC)','Davis and Elkins College (WV)','Davis College (NY)','Daytona State College (FL)','Dean College (MA)','Defiance College (OH)','Delaware State University (DE)','Delaware Valley University (PA)','Delta State University (MS)','Denison University (OH)','DePaul University (IL)','DePauw University (IN)','DEREE--The American College of Greece (None)','DeSales University (PA)','DeVry University (IL)','Dickinson College (PA)','Dickinson State University (ND)','Dillard University (LA)','Divine Word College (IA)','Dixie State University (UT)','Doane University (NE)','Dominican College (NY)','Dominican University (IL)','Dominican University of California (CA)','Donnelly College (KS)','Dordt College (IA)','Dowling College (NY)','Drake University (IA)','Drew University (NJ)','Drexel University (PA)','Drury University (MO)','Duke University (NC)','Dunwoody College of Technology (MN)','Duquesne University (PA)','E','Earlham College (IN)','East Carolina University (NC)','East Central University (OK)','East Georgia State College (GA)','East Stroudsburg University of Pennsylvania (PA)','East Tennessee State University (TN)','East Texas Baptist University (TX)','East-West University (IL)','Eastern Connecticut State University (CT)','Eastern Florida State College (FL)','Eastern Illinois University (IL)','Eastern Kentucky University (KY)','Eastern Mennonite University (VA)','Eastern Michigan University (MI)','Eastern Nazarene College (MA)','Eastern New Mexico University (NM)','Eastern Oregon University (OR)','Eastern University (PA)','Eastern Washington University (WA)','Eckerd College (FL)','ECPI University (VA)','Edgewood College (WI)','Edinboro University of Pennsylvania (PA)','Edward Waters College (FL)','Elizabeth City State University (NC)','Elizabethtown College (PA)','Elmhurst College (IL)','Elmira College (NY)','Elon University (NC)','Embry-Riddle Aeronautical University (FL)','Embry-Riddle Aeronautical University--Prescott (AZ)','Emerson College (MA)','Emmanuel College (GA)','Emmanuel College (MA)','Emmaus Bible College (IA)','Emory and Henry College (VA)','Emory University (GA)','Emporia State University (KS)','Endicott College (MA)','Erskine College (SC)','Escuela de Artes Plasticas de Puerto Rico (PR)','Eureka College (IL)','Evangel University (MO)','Everglades University (FL)','Evergreen State College (WA)','Excelsior College (NY)','F','Fairfield University (CT)','Fairleigh Dickinson University (NJ)','Fairmont State University (WV)','Faith Baptist Bible College and Theological Seminary (IA)','Farmingdale State College--SUNY (NY)','Fashion Institute of Design & Merchandising (CA)','Fashion Institute of Technology (NY)','Faulkner University (AL)','Fayetteville State University (NC)','Felician University (NJ)','Ferris State University (MI)','Ferrum College (VA)','Finlandia University (MI)','Fisher College (MA)','Fisk University (TN)','Fitchburg State University (MA)','Five Towns College (NY)','Flagler College (FL)','Florida A&M University (FL)','Florida Atlantic University (FL)','Florida College (FL)','Florida Gateway College (FL)','Florida Gulf Coast University (FL)','Florida Institute of Technology (FL)','Florida International University (FL)','Florida Memorial University (FL)','Florida National University--Main Campus (FL)','Florida Southern College (FL)','Florida SouthWestern State College (FL)','Florida State College--Jacksonville (FL)','Florida State University (FL)','Fontbonne University (MO)','Fordham University (NY)','Fort Hays State University (KS)','Fort Lewis College (CO)','Fort Valley State University (GA)','Framingham State University (MA)','Francis Marion University (SC)','Franciscan University of Steubenville (OH)','Frank Lloyd Wright School of Architecture (AZ)','Franklin and Marshall College (PA)','Franklin College (IN)','Franklin Pierce University (NH)','Franklin University (OH)','Franklin University Switzerland (None)','Franklin W. Olin College of Engineering (MA)','Freed-Hardeman University (TN)','Fresno Pacific University (CA)','Friends University (KS)','Frostburg State University (MD)','Furman University (SC)','G','Gallaudet University (DC)','Gannon University (PA)','Gardner-Webb University (NC)','Geneva College (PA)','George Fox University (OR)','George Mason University (VA)','George Washington University (DC)','Georgetown College (KY)','Georgetown University (DC)','Georgia College & State University (GA)','Georgia Gwinnett College (GA)','Georgia Institute of Technology (GA)','Georgia Southern University (GA)','Georgia Southwestern State University (GA)','Georgia State University (GA)','Georgian Court University (NJ)','Gettysburg College (PA)','Glenville State College (WV)','God\'s Bible School and College (OH)','Goddard College (VT)','Golden Gate University (CA)','Goldey-Beacom College (DE)','Goldfarb School of Nursing at Barnes-Jewish College (MO)','Gonzaga University (WA)','Gordon College (MA)','Gordon State College (GA)','Goshen College (IN)','Goucher College (MD)','Governors State University (IL)','Grace Bible College (MI)','Grace College and Seminary (IN)','Grace University (NE)','Graceland University (IA)','Grambling State University (LA)','Grand Canyon University (AZ)','Grand Valley State University (MI)','Grand View University (IA)','Granite State College (NH)','Gratz College (PA)','Great Basin College (NV)','Great Lakes Christian College (MI)','Green Mountain College (VT)','Greensboro College (NC)','Greenville College (IL)','Grinnell College (IA)','Grove City College (PA)','Guilford College (NC)','Gulf Coast State College (FL)','Gustavus Adolphus College (MN)','Gwynedd Mercy University (PA)','H','Hamilton College (NY)','Hamline University (MN)','Hampden-Sydney College (VA)','Hampshire College (MA)','Hampton University (VA)','Hannibal-LaGrange University (MO)','Hanover College (IN)','Hardin-Simmons University (TX)','Harding University (AR)','Harris-Stowe State University (MO)','Harrisburg University of Science and Technology (PA)','Hartwick College (NY)','Harvard University (MA)','Harvey Mudd College (CA)','Haskell Indian Nations University (KS)','Hastings College (NE)','Haverford College (PA)','Hawaii Pacific University (HI)','Hebrew Theological College (IL)','Heidelberg University (OH)','Hellenic College (MA)','Henderson State University (AR)','Hendrix College (AR)','Heritage University (WA)','Herzing University (WI)','High Point University (NC)','Hilbert College (NY)','Hillsdale College (MI)','Hiram College (OH)','Hobart and William Smith Colleges (NY)','Hodges University (FL)','Hofstra University (NY)','Hollins University (VA)','Holy Apostles College and Seminary (CT)','Holy Cross College (IN)','Holy Family University (PA)','Holy Names University (CA)','Hood College (MD)','Hope College (MI)','Hope International University (CA)','Houghton College (NY)','Houston Baptist University (TX)','Howard Payne University (TX)','Howard University (DC)','Hult International Business School (CA)','Humboldt State University (CA)','Humphreys College (CA)','Huntingdon College (AL)','Huntington University (IN)','Husson University (ME)','Huston-Tillotson University (TX)','I','Idaho State University (ID)','Illinois College (IL)','Illinois Institute of Art--Chicago (IL)','Illinois Institute of Technology (IL)','Illinois State University (IL)','Illinois Wesleyan University (IL)','Immaculata University (PA)','Indian River State College (FL)','Indiana Institute of Technology (IN)','Indiana State University (IN)','Indiana University East (IN)','Indiana University Northwest (IN)','Indiana University of Pennsylvania (PA)','Indiana University Southeast (IN)','Indiana University--Bloomington (IN)','Indiana University--Kokomo (IN)','Indiana University--South Bend (IN)','Indiana University-Purdue University--Fort Wayne (IN)','Indiana University-Purdue University--Indianapolis (IN)','Indiana Wesleyan University (IN)','Institute of American Indian Arts (NM)','Inter American University of Puerto Rico--Aguadilla (PR)','Inter American University of Puerto Rico--Arecibo (PR)','Inter American University of Puerto Rico--Barranquitas (PR)','Inter American University of Puerto Rico--Bayamon (PR)','Inter American University of Puerto Rico--Fajardo (PR)','Inter American University of Puerto Rico--Guayama (PR)','Inter American University of Puerto Rico--Metropolitan Campus (PR)','Inter American University of Puerto Rico--Ponce (PR)','Inter American University of Puerto Rico--San German (PR)','International College of the Cayman Islands (None)','Iona College (NY)','Iowa State University (IA)','Iowa Wesleyan University (IA)','Ithaca College (NY)','J','Jackson College (MI)','Jackson State University (MS)','Jacksonville State University (AL)','Jacksonville University (FL)','James Madison University (VA)','Jamestown Business College (NY)','Jarvis Christian College (TX)','Jewish Theological Seminary of America (NY)','John Brown University (AR)','John Carroll University (OH)','John F. Kennedy University (CA)','John Paul the Great Catholic University (CA)','Johns Hopkins University (MD)','Johnson & Wales University (RI)','Johnson C. Smith University (NC)','Johnson State College (VT)','Johnson University (FL)','Johnson University (TN)','Jones International University (CO)','Judson College (AL)','Judson University (IL)','Juilliard School (NY)','Juniata College (PA)','K','Kalamazoo College (MI)','Kansas City Art Institute (MO)','Kansas State University (KS)','Kansas Wesleyan University (KS)','Kaplan University (IA)','Kean University (NJ)','Keene State College (NH)','Keiser University (FL)','Kendall College (IL)','Kennesaw State University (GA)','Kent State University (OH)','Kentucky Christian University (KY)','Kentucky State University (KY)','Kentucky Wesleyan College (KY)','Kenyon College (OH)','Kettering College (OH)','Kettering University (MI)','Keuka College (NY)','Keystone College (PA)','King University (TN)','King\'s College (PA)','Knox College (IL)','Kutztown University of Pennsylvania (PA)','Kuyper College (MI)','L','La Roche College (PA)','La Salle University (PA)','La Sierra University (CA)','Lafayette College (PA)','LaGrange College (GA)','Laguna College of Art and Design (CA)','Lake Erie College (OH)','Lake Forest College (IL)','Lake Superior State University (MI)','Lake Washington Institute of Technology (WA)','Lake-Sumter State College (FL)','Lakeland College (WI)','Lakeview College of Nursing (IL)','Lamar University (TX)','Lancaster Bible College (PA)','Lander University (SC)','Landmark College (VT)','Lane College (TN)','Langston University (OK)','Lasell College (MA)','Lawrence Technological University (MI)','Lawrence University (WI)','Le Moyne College (NY)','Lebanese American University (None)','Lebanon Valley College (PA)','Lee University (TN)','Lees-McRae College (NC)','Lehigh University (PA)','LeMoyne-Owen College (TN)','Lenoir-Rhyne University (NC)','Lesley University (MA)','LeTourneau University (TX)','Lewis & Clark College (OR)','Lewis University (IL)','Lewis-Clark State College (ID)','Liberty University (VA)','Life Pacific College (CA)','Life University (GA)','LIM College (NY)','Limestone College (SC)','Lincoln Christian University (IL)','Lincoln College (IL)','Lincoln College of New England--Southington (CT)','Lincoln Memorial University (TN)','Lincoln University (MO)','Lincoln University (PA)','Lindenwood University (MO)','Lindsey Wilson College (KY)','Linfield College (OR)','Lipscomb University (TN)','LIU Post (NY)','Livingstone College (NC)','Lock Haven University of Pennsylvania (PA)','Loma Linda University (CA)','Longwood University (VA)','Loras College (IA)','Louisiana College (LA)','Louisiana State University Health Sciences Center (LA)','Louisiana State University--Alexandria (LA)','Louisiana State University--Baton Rouge (LA)','Louisiana State University--Shreveport (LA)','Louisiana Tech University (LA)','Lourdes University (OH)','Loyola Marymount University (CA)','Loyola University Chicago (IL)','Loyola University Maryland (MD)','Loyola University New Orleans (LA)','Lubbock Christian University (TX)','Luther College (IA)','Lycoming College (PA)','Lynchburg College (VA)','Lyndon State College (VT)','Lynn University (FL)','Lyon College (AR)','M','Macalester College (MN)','MacMurray College (IL)','Madonna University (MI)','Maharishi University of Management (IA)','Maine College of Art (ME)','Maine Maritime Academy (ME)','Malone University (OH)','Manchester University (IN)','Manhattan Christian College (KS)','Manhattan College (NY)','Manhattan School of Music (NY)','Manhattanville College (NY)','Mansfield University of Pennsylvania (PA)','Maranatha Baptist University (WI)','Maria College of Albany (NY)','Marian University (IN)','Marian University (WI)','Marietta College (OH)','Marist College (NY)','Marlboro College (VT)','Marquette University (WI)','Mars Hill University (NC)','Marshall University (WV)','Martin Luther College (MN)','Martin Methodist College (TN)','Martin University (IN)','Mary Baldwin College (VA)','Marygrove College (MI)','Maryland Institute College of Art (MD)','Marylhurst University (OR)','Marymount California University (CA)','Marymount Manhattan College (NY)','Marymount University (VA)','Maryville College (TN)','Maryville University of St. Louis (MO)','Marywood University (PA)','Massachusetts College of Art and Design (MA)','Massachusetts College of Liberal Arts (MA)','Massachusetts Institute of Technology (MA)','Massachusetts Maritime Academy (MA)','Master\'s College and Seminary (CA)','Mayville State University (ND)','McDaniel College (MD)','McGill University (None)','McKendree University (IL)','McMurry University (TX)','McNeese State University (LA)','McPherson College (KS)','MCPHS University (MA)','Medaille College (NY)','Medical University of South Carolina (SC)','Memorial University of Newfoundland (None)','Memphis College of Art (TN)','Menlo College (CA)','Mercer University (GA)','Mercy College (NY)','Mercy College of Health Sciences (IA)','Mercy College of Ohio (OH)','Mercyhurst University (PA)','Meredith College (NC)','Merrimack College (MA)','Messiah College (PA)','Methodist University (NC)','Metropolitan College of New York (NY)','Metropolitan State University (MN)','Metropolitan State University of Denver (CO)','Miami Dade College (FL)','Miami International University of Art & Design (FL)','Miami University--Oxford (OH)','Michigan State University (MI)','Michigan Technological University (MI)','Mid-America Christian University (OK)','Mid-Atlantic Christian University (NC)','MidAmerica Nazarene University (KS)','Middle Georgia State University (GA)','Middle Tennessee State University (TN)','Middlebury College (VT)','Midland College (TX)','Midland University (NE)','Midstate College (IL)','Midway University (KY)','Midwestern State University (TX)','Miles College (AL)','Millersville University of Pennsylvania (PA)','Milligan College (TN)','Millikin University (IL)','Mills College (CA)','Millsaps College (MS)','Milwaukee Institute of Art and Design (WI)','Milwaukee School of Engineering (WI)','Minneapolis College of Art and Design (MN)','Minnesota State University--Mankato (MN)','Minnesota State University--Moorhead (MN)','Minot State University (ND)','Misericordia University (PA)','Mississippi College (MS)','Mississippi State University (MS)','Mississippi University for Women (MS)','Mississippi Valley State University (MS)','Missouri Baptist University (MO)','Missouri Southern State University (MO)','Missouri State University (MO)','Missouri University of Science & Technology (MO)','Missouri Valley College (MO)','Missouri Western State University (MO)','Mitchell College (CT)','Molloy College (NY)','Monmouth College (IL)','Monmouth University (NJ)','Monroe College (NY)','Montana State University (MT)','Montana State University--Billings (MT)','Montana State University--Northern (MT)','Montana Tech of the University of Montana (MT)','Montclair State University (NJ)','Monterrey Institute of Technology and Higher Education--Monterrey (None)','Montreat College (NC)','Montserrat College of Art (MA)','Moody Bible Institute (IL)','Moore College of Art & Design (PA)','Moravian College (PA)','Morehead State University (KY)','Morehouse College (GA)','Morgan State University (MD)','Morningside College (IA)','Morris College (SC)','Morrisville State College (NY)','Mount Aloysius College (PA)','Mount Angel Seminary (OR)','Mount Carmel College of Nursing (OH)','Mount Holyoke College (MA)','Mount Ida College (MA)','Mount Marty College (SD)','Mount Mary University (WI)','Mount Mercy University (IA)','Mount Saint Mary\'s University (CA)','Mount St. Joseph University (OH)','Mount St. Mary College (NY)','Mount St. Mary\'s University (MD)','Mount Vernon Nazarene University (OH)','Mount Washington College (NH)','Muhlenberg College (PA)','Multnomah University (OR)','Murray State University (KY)','Muskingum University (OH)','N','Naropa University (CO)','National American University (SD)','National Graduate School of Quality Management (MA)','National Louis University (IL)','National University (CA)','Nazarene Bible College (CO)','Nazareth College (NY)','Nebraska Methodist College (NE)','Nebraska Wesleyan University (NE)','Neumann University (PA)','Nevada State College (NV)','New College of Florida (FL)','New England College (NH)','New England College of Business and Finance (MA)','New England College of Optometry (MA)','New England Conservatory of Music (MA)','New England Institute of Art (MA)','New England Institute of Technology (RI)','New Hampshire Institute of Art (NH)','New Jersey City University (NJ)','New Jersey Institute of Technology (NJ)','New Mexico Highlands University (NM)','New Mexico Institute of Mining and Technology (NM)','New Mexico State University (NM)','New Orleans Baptist Theological Seminary (LA)','New School (NY)','New York Institute of Technology (NY)','New York University (NY)','Newberry College (SC)','Newbury College (MA)','Newman University (KS)','NewSchool of Architecture and Design (CA)','Niagara University (NY)','Nicholls State University (LA)','Nichols College (MA)','Norfolk State University (VA)','North Carolina A&T State University (NC)','North Carolina Central University (NC)','North Carolina State University--Raleigh (NC)','North Carolina Wesleyan College (NC)','North Central College (IL)','North Central University (MN)','North Dakota State University (ND)','North Greenville University (SC)','North Park University (IL)','North Seattle College (WA)','Northcentral University (AZ)','Northeastern Illinois University (IL)','Northeastern State University (OK)','Northeastern University (MA)','Northern Arizona University (AZ)','Northern Illinois University (IL)','Northern Kentucky University (KY)','Northern Michigan University (MI)','Northern New Mexico University (NM)','Northern State University (SD)','Northland College (WI)','Northwest Christian University (OR)','Northwest Florida State College (FL)','Northwest Missouri State University (MO)','Northwest Nazarene University (ID)','Northwest University (WA)','Northwestern College (IA)','Northwestern Health Sciences University (MN)','Northwestern Michigan College (MI)','Northwestern Oklahoma State University (OK)','Northwestern State University of Louisiana (LA)','Northwestern University (IL)','Northwood University (MI)','Norwich University (VT)','Notre Dame College of Ohio (OH)','Notre Dame de Namur University (CA)','Notre Dame of Maryland University (MD)','Nova Scotia College of Art and Design (None)','Nova Southeastern University (FL)','Nyack College (NY)','O','Oakland City University (IN)','Oakland University (MI)','Oakwood University (AL)','Oberlin College (OH)','Occidental College (CA)','Oglala Lakota College (SD)','Oglethorpe University (GA)','Ohio Christian University (OH)','Ohio Dominican University (OH)','Ohio Northern University (OH)','Ohio State University--Columbus (OH)','Ohio University (OH)','Ohio Valley University (WV)','Ohio Wesleyan University (OH)','Oklahoma Baptist University (OK)','Oklahoma Christian University (OK)','Oklahoma City University (OK)','Oklahoma Panhandle State University (OK)','Oklahoma State University (OK)','Oklahoma State University Institute of Technology--Okmulgee (OK)','Oklahoma State University--Oklahoma City (OK)','Oklahoma Wesleyan University (OK)','Old Dominion University (VA)','Olivet College (MI)','Olivet Nazarene University (IL)','Olympic College (WA)','Oral Roberts University (OK)','Oregon College of Art and Craft (OR)','Oregon Health and Science University (OR)','Oregon Institute of Technology (OR)','Oregon State University (OR)','Otis College of Art and Design (CA)','Ottawa University (KS)','Otterbein University (OH)','Ouachita Baptist University (AR)','Our Lady of Holy Cross College (LA)','Our Lady of the Lake College (LA)','Our Lady of the Lake University (TX)','P','Pace University (NY)','Pacific Lutheran University (WA)','Pacific Northwest College of Art (OR)','Pacific Oaks College (CA)','Pacific Union College (CA)','Pacific University (OR)','Paine College (GA)','Palm Beach Atlantic University (FL)','Palm Beach State College (FL)','Palmer College of Chiropractic (IA)','Park University (MO)','Parker University (TX)','Paul Smith\'s College (NY)','Peirce College (PA)','Peninsula College (WA)','Pennsylvania Academy of the Fine Arts (PA)','Pennsylvania College of Art and Design (PA)','Pennsylvania College of Technology (PA)','Pennsylvania State University--Erie, The Behrend College (PA)','Pennsylvania State University--Harrisburg (PA)','Pennsylvania State University--University Park (PA)','Pensacola State College (FL)','Pepperdine University (CA)','Peru State College (NE)','Pfeiffer University (NC)','Philadelphia University (PA)','Philander Smith College (AR)','Piedmont College (GA)','Pine Manor College (MA)','Pittsburg State University (KS)','Pitzer College (CA)','Plaza College (NY)','Plymouth State University (NH)','Point Loma Nazarene University (CA)','Point Park University (PA)','Point University (GA)','Polk State College (FL)','Pomona College (CA)','Pontifical Catholic University of Puerto Rico (PR)','Pontifical College Josephinum (OH)','Portland State University (OR)','Post University (CT)','Prairie View A&M University (TX)','Pratt Institute (NY)','Presbyterian College (SC)','Prescott College (AZ)','Presentation College (SD)','Princeton University (NJ)','Principia College (IL)','Providence Christian College (CA)','Providence College (RI)','Puerto Rico Conservatory of Music (PR)','Purchase College--SUNY (NY)','Purdue University--North Central (IN)','Purdue University--West Lafayette (IN)','Q','Queens University of Charlotte (NC)','Quincy University (IL)','Quinnipiac University (CT)','R','Radford University (VA)','Ramapo College of New Jersey (NJ)','Randolph College (VA)','Randolph-Macon College (VA)','Ranken Technical College (MO)','Reed College (OR)','Regent University (VA)','Regent\'s American College London (None)','Regis College (MA)','Regis University (CO)','Reinhardt University (GA)','Rensselaer Polytechnic Institute (NY)','Research College of Nursing (MO)','Resurrection University (IL)','Rhode Island College (RI)','Rhode Island School of Design (RI)','Rhodes College (TN)','Rice University (TX)','Richmond--The American International University in London (None)','Rider University (NJ)','Ringling College of Art and Design (FL)','Ripon College (WI)','Rivier University (NH)','Roanoke College (VA)','Robert B. Miller College (MI)','Robert Morris University (IL)','Robert Morris University (PA)','Roberts Wesleyan College (NY)','Rochester College (MI)','Rochester Institute of Technology (NY)','Rockford University (IL)','Rockhurst University (MO)','Rocky Mountain College (MT)','Rocky Mountain College of Art and Design (CO)','Roger Williams University (RI)','Rogers State University (OK)','Rollins College (FL)','Roosevelt University (IL)','Rosalind Franklin University of Medicine and Science (IL)','Rose-Hulman Institute of Technology (IN)','Rosemont College (PA)','Rowan University (NJ)','Rush University (IL)','Rust College (MS)','Rutgers University--Camden (NJ)','Rutgers University--New Brunswick (NJ)','Rutgers University--Newark (NJ)','Ryerson University (None)','S','Sacred Heart Major Seminary (MI)','Sacred Heart University (CT)','Saginaw Valley State University (MI)','Saint Johns River State College (FL)','Saint Leo University (FL)','Saint Louis University (MO)','Saint Mary-of-the-Woods College (IN)','Saint Vincent College (PA)','Salem College (NC)','Salem International University (WV)','Salem State University (MA)','Salisbury University (MD)','Salish Kootenai College (MT)','Salve Regina University (RI)','Sam Houston State University (TX)','Samford University (AL)','Samuel Merritt University (CA)','San Diego Christian College (CA)','San Diego State University (CA)','San Francisco Art Institute (CA)','San Francisco Conservatory of Music (CA)','San Francisco State University (CA)','San Jose State University (CA)','Santa Clara University (CA)','Santa Fe College (FL)','Santa Fe University of Art and Design (NM)','Sarah Lawrence College (NY)','Savannah College of Art and Design (GA)','Savannah State University (GA)','School of the Art Institute of Chicago (IL)','School of Visual Arts (NY)','Schreiner University (TX)','Scripps College (CA)','Seattle Central College (WA)','Seattle Pacific University (WA)','Seattle University (WA)','Seminole State College of Florida (FL)','Seton Hall University (NJ)','Seton Hill University (PA)','Sewanee--University of the South (TN)','Shaw University (NC)','Shawnee State University (OH)','Shenandoah University (VA)','Shepherd University (WV)','Shimer College (IL)','Shippensburg University of Pennsylvania (PA)','Shorter University (GA)','Siena College (NY)','Siena Heights University (MI)','Sierra Nevada College (NV)','Silver Lake College (WI)','Simmons College (MA)','Simon Fraser University (None)','Simpson College (IA)','Simpson University (CA)','Sinte Gleska University (SD)','Sitting Bull College (ND)','Skidmore College (NY)','Slippery Rock University of Pennsylvania (PA)','Smith College (MA)','Snow College (UT)','Sojourner-Douglass College (MD)','Soka University of America (CA)','Sonoma State University (CA)','South Carolina State University (SC)','South College (TN)','South Dakota School of Mines and Technology (SD)','South Dakota State University (SD)','South Florida State College (FL)','South Georgia State College (GA)','South Seattle College (WA)','South Texas College (TX)','South University (GA)','Southeast Missouri State University (MO)','Southeastern Baptist Theological Seminary (NC)','Southeastern Louisiana University (LA)','Southeastern Oklahoma State University (OK)','Southeastern University (FL)','Southern Adventist University (TN)','Southern Arkansas University (AR)','Southern Baptist Theological Seminary (KY)','Southern California Institute of Architecture (CA)','Southern Connecticut State University (CT)','Southern Illinois University--Carbondale (IL)','Southern Illinois University--Edwardsville (IL)','Southern Methodist University (TX)','Southern Nazarene University (OK)','Southern New Hampshire University (NH)','Southern Oregon University (OR)','Southern University and A&M College (LA)','Southern University--New Orleans (LA)','Southern Utah University (UT)','Southern Vermont College (VT)','Southern Virginia University (VA)','Southern Wesleyan University (SC)','Southwest Baptist University (MO)','Southwest Minnesota State University (MN)','Southwest University of Visual Arts (AZ)','Southwestern Adventist University (TX)','Southwestern Assemblies of God University (TX)','Southwestern Christian College (TX)','Southwestern Christian University (OK)','Southwestern College (KS)','Southwestern Oklahoma State University (OK)','Southwestern University (TX)','Spalding University (KY)','Spelman College (GA)','Spring Arbor University (MI)','Spring Hill College (AL)','Springfield College (MA)','St. Ambrose University (IA)','St. Anselm College (NH)','St. Anthony College of Nursing (IL)','St. Augustine College (IL)','St. Augustine\'s University (NC)','St. Bonaventure University (NY)','St. Catherine University (MN)','St. Charles Borromeo Seminary (PA)','St. Cloud State University (MN)','St. Edward\'s University (TX)','St. Francis College (NY)','St. Francis Medical Center College of Nursing (IL)','St. Francis University (PA)','St. Gregory\'s University (OK)','St. John Fisher College (NY)','St. John Vianney College Seminary (FL)','St. John\'s College (MD)','St. John\'s College (NM)','St. John\'s College (IL)','St. John\'s University (MN)','St. John\'s University (NY)','St. Joseph Seminary College (LA)','St. Joseph\'s College (IN)','St. Joseph\'s College (ME)','St. Joseph\'s College New York (NY)','St. Joseph\'s University (PA)','St. Lawrence University (NY)','St. Louis College of Pharmacy (MO)','St. Luke\'s College of Health Sciences (MO)','St. Martin\'s University (WA)','St. Mary\'s College (IN)','St. Mary\'s College of California (CA)','St. Mary\'s College of Maryland (MD)','St. Mary\'s University of Minnesota (MN)','St. Mary\'s University of San Antonio (TX)','St. Michael\'s College (VT)','St. Norbert College (WI)','St. Olaf College (MN)','St. Peter\'s University (NJ)','St. Petersburg College (FL)','St. Thomas Aquinas College (NY)','St. Thomas University (FL)','St. Xavier University (IL)','Stanford University (CA)','State College of Florida--Manatee-Sarasota (FL)','Stephen F. Austin State University (TX)','Stephens College (MO)','Sterling College (KS)','Sterling College (VT)','Stetson University (FL)','Stevens Institute of Technology (NJ)','Stevenson University (MD)','Stillman College (AL)','Stockton University (NJ)','Stonehill College (MA)','Stony Brook University--SUNY (NY)','Strayer University (DC)','Suffolk University (MA)','Sul Ross State University (TX)','Sullivan University (KY)','Summit University (PA)','SUNY Buffalo State (NY)','SUNY College of Agriculture and Technology--Cobleskill (NY)','SUNY College of Environmental Science and Forestry (NY)','SUNY College of Technology--Alfred (NY)','SUNY College of Technology--Canton (NY)','SUNY College of Technology--Delhi (NY)','SUNY College--Cortland (NY)','SUNY College--Old Westbury (NY)','SUNY College--Oneonta (NY)','SUNY College--Potsdam (NY)','SUNY Downstate Medical Center (NY)','SUNY Empire State College (NY)','SUNY Maritime College (NY)','SUNY Polytechnic Institute (NY)','SUNY Upstate Medical University (NY)','SUNY--Fredonia (NY)','SUNY--Geneseo (NY)','SUNY--New Paltz (NY)','SUNY--Oswego (NY)','SUNY--Plattsburgh (NY)','Susquehanna University (PA)','Swarthmore College (PA)','Sweet Briar College (VA)','Syracuse University (NY)','T','Tabor College (KS)','Talladega College (AL)','Tarleton State University (TX)','Taylor University (IN)','Temple University (PA)','Tennessee State University (TN)','Tennessee Technological University (TN)','Tennessee Wesleyan College (TN)','Texas A&M International University (TX)','Texas A&M University--College Station (TX)','Texas A&M University--Commerce (TX)','Texas A&M University--Corpus Christi (TX)','Texas A&M University--Kingsville (TX)','Texas A&M University--Texarkana (TX)','Texas Christian University (TX)','Texas College (TX)','Texas Lutheran University (TX)','Texas Southern University (TX)','Texas State University (TX)','Texas Tech University (TX)','Texas Tech University Health Sciences Center (TX)','Texas Wesleyan University (TX)','Texas Woman\'s University (TX)','The Art Institute of Philadelphia (PA)','The Catholic University of America (DC)','The Citadel (SC)','The College of Westchester (NY)','The King\'s College (NY)','The Sage Colleges (NY)','Thiel College (PA)','Thomas Aquinas College (CA)','Thomas College (ME)','Thomas Edison State University (NJ)','Thomas Jefferson University (PA)','Thomas More College (KY)','Thomas More College of Liberal Arts (NH)','Thomas University (GA)','Tiffin University (OH)','Tilburg University (None)','Toccoa Falls College (GA)','Tougaloo College (MS)','Touro College (NY)','Towson University (MD)','Transylvania University (KY)','Trent University (None)','Trevecca Nazarene University (TN)','Trident University International (CA)','Trine University (IN)','Trinity Christian College (IL)','Trinity College (CT)','Trinity College of Nursing & Health Sciences (IL)','Trinity International University (IL)','Trinity Lutheran College (WA)','Trinity University (TX)','Trinity Washington University (DC)','Trinity Western University (None)','Troy University (AL)','Truett McConnell College (GA)','Truman State University (MO)','Tufts University (MA)','Tulane University (LA)','Tusculum College (TN)','Tuskegee University (AL)','U','Union College (KY)','Union College (NE)','Union College (NY)','Union Institute and University (OH)','Union University (TN)','United States Air Force Academy (CO)','United States Coast Guard Academy (CT)','United States International University--Kenya (None)','United States Merchant Marine Academy (NY)','United States Military Academy (NY)','United States Naval Academy (MD)','United States Sports Academy (AL)','United States University (CA)','Unity College (ME)','Universidad Adventista de las Antillas (PR)','Universidad del Este (PR)','Universidad del Turabo (PR)','Universidad Metropolitana (PR)','Universidad Politecnica de Puerto Rico (PR)','University at Albany--SUNY (NY)','University at Buffalo--SUNY (NY)','University of Advancing Technology (AZ)','University of Akron (OH)','University of Alabama (AL)','University of Alabama--Birmingham (AL)','University of Alabama--Huntsville (AL)','University of Alaska--Anchorage (AK)','University of Alaska--Fairbanks (AK)','University of Alaska--Southeast (AK)','University of Alberta (None)','University of Arizona (AZ)','University of Arkansas (AR)','University of Arkansas for Medical Sciences (AR)','University of Arkansas--Fort Smith (AR)','University of Arkansas--Little Rock (AR)','University of Arkansas--Monticello (AR)','University of Arkansas--Pine Bluff (AR)','University of Baltimore (MD)','University of Bridgeport (CT)','University of British Columbia (None)','University of Calgary (None)','University of California--Berkeley (CA)','University of California--Davis (CA)','University of California--Irvine (CA)','University of California--Los Angeles (CA)','University of California--Merced (CA)','University of California--Riverside (CA)','University of California--San Diego (CA)','University of California--Santa Barbara (CA)','University of California--Santa Cruz (CA)','University of Central Arkansas (AR)','University of Central Florida (FL)','University of Central Missouri (MO)','University of Central Oklahoma (OK)','University of Charleston (WV)','University of Chicago (IL)','University of Cincinnati (OH)','University of Cincinnati--UC Blue Ash College (OH)','University of Colorado--Boulder (CO)','University of Colorado--Colorado Springs (CO)','University of Colorado--Denver (CO)','University of Connecticut (CT)','University of Dallas (TX)','University of Dayton (OH)','University of Delaware (DE)','University of Denver (CO)','University of Detroit Mercy (MI)','University of Dubuque (IA)','University of Evansville (IN)','University of Findlay (OH)','University of Florida (FL)','University of Georgia (GA)','University of Great Falls (MT)','University of Guam (GU)','University of Guelph (None)','University of Hartford (CT)','University of Hawaii--Hilo (HI)','University of Hawaii--Manoa (HI)','University of Hawaii--Maui College (HI)','University of Hawaii--West Oahu (HI)','University of Houston (TX)','University of Houston--Clear Lake (TX)','University of Houston--Downtown (TX)','University of Houston--Victoria (TX)','University of Idaho (ID)','University of Illinois--Chicago (IL)','University of Illinois--Springfield (IL)','University of Illinois--Urbana-Champaign (IL)','University of Indianapolis (IN)','University of Iowa (IA)','University of Jamestown (ND)','University of Kansas (KS)','University of Kentucky (KY)','University of La Verne (CA)','University of Louisiana--Lafayette (LA)','University of Louisiana--Monroe (LA)','University of Louisville (KY)','University of Maine (ME)','University of Maine--Augusta (ME)','University of Maine--Farmington (ME)','University of Maine--Fort Kent (ME)','University of Maine--Machias (ME)','University of Maine--Presque Isle (ME)','University of Mary (ND)','University of Mary Hardin-Baylor (TX)','University of Mary Washington (VA)','University of Maryland University College (MD)','University of Maryland--Baltimore (MD)','University of Maryland--Baltimore County (MD)','University of Maryland--College Park (MD)','University of Maryland--Eastern Shore (MD)','University of Massachusetts--Amherst (MA)','University of Massachusetts--Boston (MA)','University of Massachusetts--Dartmouth (MA)','University of Massachusetts--Lowell (MA)','University of Memphis (TN)','University of Miami (FL)','University of Michigan--Ann Arbor (MI)','University of Michigan--Dearborn (MI)','University of Michigan--Flint (MI)','University of Minnesota--Crookston (MN)','University of Minnesota--Duluth (MN)','University of Minnesota--Morris (MN)','University of Minnesota--Twin Cities (MN)','University of Mississippi (MS)','University of Missouri (MO)','University of Missouri--Kansas City (MO)','University of Missouri--St. Louis (MO)','University of Mobile (AL)','University of Montana (MT)','University of Montana--Western (MT)','University of Montevallo (AL)','University of Mount Olive (NC)','University of Mount Union (OH)','University of Nebraska Medical Center (NE)','University of Nebraska--Kearney (NE)','University of Nebraska--Lincoln (NE)','University of Nebraska--Omaha (NE)','University of Nevada--Las Vegas (NV)','University of Nevada--Reno (NV)','University of New Brunswick (None)','University of New England (ME)','University of New Hampshire (NH)','University of New Haven (CT)','University of New Mexico (NM)','University of New Orleans (LA)','University of North Alabama (AL)','University of North Carolina School of the Arts (NC)','University of North Carolina--Asheville (NC)','University of North Carolina--Chapel Hill (NC)','University of North Carolina--Charlotte (NC)','University of North Carolina--Greensboro (NC)','University of North Carolina--Pembroke (NC)','University of North Carolina--Wilmington (NC)','University of North Dakota (ND)','University of North Florida (FL)','University of North Georgia (GA)','University of North Texas (TX)','University of North Texas--Dallas (TX)','University of Northern Colorado (CO)','University of Northern Iowa (IA)','University of Northwestern Ohio (OH)','University of Northwestern--St. Paul (MN)','University of Notre Dame (IN)','University of Oklahoma (OK)','University of Oklahoma Health Sciences Center (OK)','University of Oregon (OR)','University of Ottawa (None)','University of Pennsylvania (PA)','University of Phoenix (AZ)','University of Pikeville (KY)','University of Pittsburgh (PA)','University of Portland (OR)','University of Prince Edward Island (None)','University of Puerto Rico--Aguadilla (PR)','University of Puerto Rico--Arecibo (PR)','University of Puerto Rico--Bayamon (PR)','University of Puerto Rico--Cayey (PR)','University of Puerto Rico--Humacao (PR)','University of Puerto Rico--Mayaguez (PR)','University of Puerto Rico--Medical Sciences Campus (PR)','University of Puerto Rico--Ponce (PR)','University of Puerto Rico--Rio Piedras (PR)','University of Puget Sound (WA)','University of Redlands (CA)','University of Regina (None)','University of Rhode Island (RI)','University of Richmond (VA)','University of Rio Grande (OH)','University of Rochester (NY)','University of Saint Francis (IN)','University of San Diego (CA)','University of San Francisco (CA)','University of Saskatchewan (None)','University of Science and Arts of Oklahoma (OK)','University of Scranton (PA)','University of Sioux Falls (SD)','University of South Alabama (AL)','University of South Carolina (SC)','University of South Carolina--Aiken (SC)','University of South Carolina--Beaufort (SC)','University of South Carolina--Upstate (SC)','University of South Dakota (SD)','University of South Florida (FL)','University of South Florida--St. Petersburg (FL)','University of Southern California (CA)','University of Southern Indiana (IN)','University of Southern Maine (ME)','University of Southern Mississippi (MS)','University of St. Francis (IL)','University of St. Joseph (CT)','University of St. Mary (KS)','University of St. Thomas (MN)','University of St. Thomas (TX)','University of Tampa (FL)','University of Tennessee (TN)','University of Tennessee--Chattanooga (TN)','University of Tennessee--Martin (TN)','University of Texas Health Science Center--Houston (TX)','University of Texas Health Science Center--San Antonio (TX)','University of Texas Medical Branch--Galveston (TX)','University of Texas of the Permian Basin (TX)','University of Texas--Arlington (TX)','University of Texas--Austin (TX)','University of Texas--Dallas (TX)','University of Texas--El Paso (TX)','University of Texas--Rio Grande Valley (TX)','University of Texas--San Antonio (TX)','University of Texas--Tyler (TX)','University of the Antelope Valley (CA)','University of the Arts (PA)','University of the Cumberlands (KY)','University of the District of Columbia (DC)','University of the Incarnate Word (TX)','University of the Ozarks (AR)','University of the Pacific (CA)','University of the Potomac (DC)','University of the Sacred Heart (PR)','University of the Sciences (PA)','University of the Southwest (NM)','University of the Virgin Islands (VI)','University of the West (CA)','University of Toledo (OH)','University of Toronto (None)','University of Tulsa (OK)','University of Utah (UT)','University of Valley Forge (PA)','University of Vermont (VT)','University of Victoria (None)','University of Virginia (VA)','University of Virginia--Wise (VA)','University of Washington (WA)','University of Waterloo (None)','University of West Alabama (AL)','University of West Florida (FL)','University of West Georgia (GA)','University of Windsor (None)','University of Winnipeg (None)','University of Wisconsin--Eau Claire (WI)','University of Wisconsin--Green Bay (WI)','University of Wisconsin--La Crosse (WI)','University of Wisconsin--Madison (WI)','University of Wisconsin--Milwaukee (WI)','University of Wisconsin--Oshkosh (WI)','University of Wisconsin--Parkside (WI)','University of Wisconsin--Platteville (WI)','University of Wisconsin--River Falls (WI)','University of Wisconsin--Stevens Point (WI)','University of Wisconsin--Stout (WI)','University of Wisconsin--Superior (WI)','University of Wisconsin--Whitewater (WI)','University of Wyoming (WY)','Upper Iowa University (IA)','Urbana University (OH)','Ursinus College (PA)','Ursuline College (OH)','Utah State University (UT)','Utah Valley University (UT)','Utica College (NY)','V','Valdosta State University (GA)','Valencia College (FL)','Valley City State University (ND)','Valparaiso University (IN)','Vanderbilt University (TN)','VanderCook College of Music (IL)','Vanguard University of Southern California (CA)','Vassar College (NY)','Vaughn College of Aeronautics and Technology (NY)','Vermont Technical College (VT)','Villa Maria College (NY)','Villanova University (PA)','Vincennes University (IN)','Virginia Commonwealth University (VA)','Virginia Military Institute (VA)','Virginia State University (VA)','Virginia Tech (VA)','Virginia Union University (VA)','Virginia Wesleyan College (VA)','Viterbo University (WI)','Voorhees College (SC)','W','Wabash College (IN)','Wade College (TX)','Wagner College (NY)','Wake Forest University (NC)','Walden University (MN)','Waldorf College (IA)','Walla Walla University (WA)','Walsh College of Accountancy and Business Administration (MI)','Walsh University (OH)','Warner Pacific College (OR)','Warner University (FL)','Warren Wilson College (NC)','Wartburg College (IA)','Washburn University (KS)','Washington Adventist University (MD)','Washington and Jefferson College (PA)','Washington and Lee University (VA)','Washington College (MD)','Washington State University (WA)','Washington University in St. Louis (MO)','Watkins College of Art, Design & Film (TN)','Wayland Baptist University (TX)','Wayne State College (NE)','Wayne State University (MI)','Waynesburg University (PA)','Webb Institute (NY)','Webber International University (FL)','Weber State University (UT)','Webster University (MO)','Welch College (TN)','Wellesley College (MA)','Wells College (NY)','Wentworth Institute of Technology (MA)','Wesley College (DE)','Wesleyan College (GA)','Wesleyan University (CT)','West Chester University of Pennsylvania (PA)','West Liberty University (WV)','West Texas A&M University (TX)','West Virginia State University (WV)','West Virginia University (WV)','West Virginia University Institute of Technology (WV)','West Virginia University--Parkersburg (WV)','West Virginia Wesleyan College (WV)','Western Carolina University (NC)','Western Connecticut State University (CT)','Western Governors University (UT)','Western Illinois University (IL)','Western International University (AZ)','Western Kentucky University (KY)','Western Michigan University (MI)','Western Nevada College (NV)','Western New England University (MA)','Western New Mexico University (NM)','Western Oregon University (OR)','Western State Colorado University (CO)','Western University (None)','Western Washington University (WA)','Westfield State University (MA)','Westminster College (MO)','Westminster College (PA)','Westminster College (UT)','Westmont College (CA)','Wheaton College (IL)','Wheaton College (MA)','Wheeling Jesuit University (WV)','Wheelock College (MA)','Whitman College (WA)','Whittier College (CA)','Whitworth University (WA)','Wichita State University (KS)','Widener University (PA)','Wilberforce University (OH)','Wiley College (TX)','Wilkes University (PA)','Willamette University (OR)','William Carey University (MS)','William Jessup University (CA)','William Jewell College (MO)','William Paterson University of New Jersey (NJ)','William Peace University (NC)','William Penn University (IA)','William Woods University (MO)','Williams Baptist College (AR)','Williams College (MA)','Wilmington College (OH)','Wilmington University (DE)','Wilson College (PA)','Wingate University (NC)','Winona State University (MN)','Winston-Salem State University (NC)','Winthrop University (SC)','Wisconsin Lutheran College (WI)','Wittenberg University (OH)','Wofford College (SC)','Woodbury University (CA)','Worcester Polytechnic Institute (MA)','Worcester State University (MA)','Wright State University (OH)','X','Xavier University (OH)','Xavier University of Louisiana (LA)','Y','Yale University (CT)','Yeshiva University (NY)','York College (NE)','York College of Pennsylvania (PA)','York University (None)','Young Harris College (GA)','Youngstown State University (OH)','College Search',)))
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
