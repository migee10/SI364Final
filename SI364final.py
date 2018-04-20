###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
## Import statements

import os
import json
import datetime
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError, RadioField, IntegerField
from wtforms.validators import Required, Length, Email, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from requests.exceptions import HTTPError
import json


# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

## All app.config values
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'passpasspasspassword'
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/deletesoon"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/deletesoon"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['HEROKU_ON'] = os.environ.get('HEROKU')

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)

api_key = 'AIzaSyAmME85rRtDtzUW9-5svLd7vcT3No6e4pQ'
API_KEY = 'AIzaSyAmME85rRtDtzUW9-5svLd7vcT3No6e4pQ'
# App addition setups
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

######################################
######## HELPER FXNS (If any) ########
######################################


#ASSOCIATION TABLE
#places can have many ratings, ratings can have many places
#search term, places
asso_table = db.Table('asso_table',db.Column('places_id', db.Integer, db.ForeignKey('places.id')), db.Column('sterm_id', db.Integer, db.ForeignKey('searchTerm.id')))

##################
##### MODELS #####
##################

class User(db.Model, UserMixin):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Places(db.Model):
    __tablename__ = 'places'
    id = db.Column(db.Integer, primary_key=True)
    business = db.Column(db.String(128))
    location = db.Column(db.String)
    ratings = db.Column(db.Float)
    rating = db.relationship('Ratings', backref='Places')

    def __repr__(self):
        return 'Your search result gave you: {}'.format(self.business)

class SearchTerm(db.Model):
    __tablename__ = 'searchTerm'
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(32), unique=True)
    places = db.relationship('Places', secondary=asso_table, backref=db.backref('places', lazy='dynamic'),lazy='dynamic')

    def __repr__(self):
        return "You searched: {}".format(self.term)

class Ratings(db.Model):
    __tablename__ = 'restaurant_ratings'
    id = db.Column(db.Integer, primary_key=True)
    placename = db.Column(db.String(200))
    rating = db.Column(db.Integer)
    price = db.Column(db.Integer)
    text_entry = db.Column(db.String(200))
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"))

    def __repr__(self):
        return "You gave {} a {}!".format(self.placename, self.rating, self.price)

class SavedList(db.Model):
    __tablename__ = 'list'
    id = db.Column(db.Integer, primary_key=True)
    place_name = db.Column(db.String(64))

    def __repr__(self):
        return "       - {}".format(self.place_name, self.id)

###################
###### FORMS ######
###################
class UpdateButtonForm(FlaskForm):
    new_place = StringField("What would you like to update the location to?", validators=[Required()])
    submit = SubmitField("Update")


class DeleteButtonForm(FlaskForm):
    submit = SubmitField("Delete")

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64)])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class SearchForm(FlaskForm):
    business = StringField("Please enter a business:", validators=[Required()])
    submit = SubmitField()

    def validate_search(self, field):
        if len(field.data.split()) < 1:
            raise ValidationError("You must enter a business name")


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RatingForm(FlaskForm):
    placename = StringField("Please enter a business you want to rate.", validators=[Required()])
    rating = StringField("Please enter your overall rating for this business (0-5, 0=worst and 5=best).", validators=[Required()])
    price = StringField('Please rate the price at this business (0-5, 0=worst and 5=best).', validators=[Required()])
    text_entry = StringField('Please enter any additional comments in the textbox below:')
    submit = SubmitField()

    def validate_ratings(self, field):
        if len(field.data.split()) < 1:
            raise ValidationError("Please make sure all fields are filled out")


class SaveForm(FlaskForm):
    your_places = StringField("Add a place to check-in", validators=[Required()])
    submit = SubmitField()


#######################
##### HELPER FXNS #####
#######################
def get_or_create_searchterm(term):
    search_term = SearchTerm.query.filter_by(term=term).first()
    if search_term:
        return search_term

    search_term = SearchTerm(term=term)
    db.session.add(search_term)
    db.session.commit()
    return search_term

def get_or_create_list(place_name):
    listname = SavedList.query.filter_by(place_name=place_name).first()
    if listname:
        return listname

    listname = SavedList(place_name=place_name)
    db.session.add(listname)
    db.session.commit()
    return listname

def get_google_data(place):
    baseurl = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=37.7749295,-122.4194155&radius=900&types=food&name="+place+"&key="+API_KEY
    params = {'b': place}
    response = requests.get(baseurl, params=params)
    data = json.loads(response.text)

    name_restaurant = {}
    for x in data['results']:
        name_restaurant = (x['0']['name'])

    print(name_restaurant)
    return (name_restaurant)
    # name = (data_son['results'][0]['name'])
    # rating = (data_son['results'][0]['rating'])
    # location = (data_son['results'][0]['vicinity'])

def make_shell_context():
    return dict( app=app, db=db, Song=Song, Artist=Artist, Album=Album)
# Add function use to manager
manager.add_command("shell", Shell(make_context=make_shell_context))

#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods = ['POST', 'GET'])
@login_required
def index():
    form = SearchForm()
    if form.validate_on_submit():
        business = form.business.data
        # find_place(business)
        newplace = Places(business = business)
        db.session.add(newplace)
        db.session.commit()
        return redirect(url_for('all_places', term = term))
    return render_template('index.html', form=form)



@app.route('/save_place')
@login_required
def save():
    form = SaveForm()
    return render_template('list_form.html', form=form)

@app.route('/saved_list', methods=["GET", "POST"])
@login_required
def saved_list():
    form=SaveForm()
    if form.validate_on_submit():
        place = form.your_places.data

        saves = get_or_create_list(place)
        # new = SavedList(place_name=place)
        # # db.session.add(new)
        # # db.session.commit()
        return redirect(url_for('all_places'))
    return render_template('list_form.html', form=form)

@app.route('/all_places', methods=["GET", "POST"])
@login_required
def all_places():
    form = DeleteButtonForm()
    places = SavedList.query.all()
    return render_template('saved_list.html', places=places, form=form)

@app.route('/list/<option>', methods=["GET","POST"])
@login_required
def new_list(option):
    form = UpdateButtonForm()
    places = SavedList.query.filter_by(place_name=option).first()
    # items = places.place_name.all()
    return render_template('update_form.html', places=places, form=form )

@app.route('/update/<name>', methods=["GET", "POST"])
@login_required
def update(name):
    form = UpdateButtonForm()
    if form.validate_on_submit():
        print("form validated")
        new_update = form.new_place.data
        s = SavedList.query.filter_by(place_name=name).first()
        s.place_name = new_update
        db.session.commit()
        flash("Updated name to: " + s.place_name)
        return redirect(url_for('all_places'))
    return render_template('update.html', name=name, form=form)

@app.route('/delete/<place>', methods=["GET", "POST"])
def delete(place):
    l = SavedList.query.filter_by(place_name=place).first()
    db.session.delete(l)
    flash("{} Deleted".format(place))
    return redirect(url_for('all_places'))


@app.route('/previously_searched', methods=["GET", "POST"])
@login_required
def previously_searched():
    previous = Places.query.all()
    return render_template('previously_searched.html', previous=previous)

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are now logged out.')
    return redirect(url_for('index'))

    # users log out
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user= User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#let users search using key words with the Google API
@app.route('/search', methods = ["GET", "POST"])
@login_required
def search():
    form = SearchForm()
    return render_template('search.html', form=form)

@app.route('/searchdata', methods = ["GET", "POST"])
def searchdata():
    form = SearchForm()
    if form.validate_on_submit():
        business = form.business.data
        search = get_or_create_searchterm(business)
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=37.7749295,-122.4194155&radius=900&types=food&name="+business+"&key="+API_KEY
        data = requests.get(url)
        data_test = data.text
        data_son = json.loads(data_test)
        name = (data_son['results'][0]['name'])
        rating = (data_son['results'][0]['rating'])
        location = (data_son['results'][0]['vicinity'])


        newname = Places(business=name, ratings=rating, location=location)
        # newrating = Places(ratings=rating)
        # newloc = Places(location=location)

        db.session.add(newname)


        db.session.commit()
        # db.session.add(newrating)
        # db.session.commit()
        # db.session.add(newloc)
        # db.session.commit()


        if data.status_code != 200:
            flash('Something went wrong, try entering again!')
            return redirect(url_for('search'))

        searchresults = json.loads(data.text)
        return render_template('placedata.html', data = searchresults)
    flash('All fields are required!')
    return redirect(url_for('search'))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('search.html', form=form)

@app.route('/enter_rating', methods=["GET", "POST"])
@login_required
def rating():
    form = RatingForm()

    if form.validate_on_submit():
        placename = form.placename.data
        rating = form.rating.data
        price = form.price.data
        text_entry = form.text_entry.data


        rating = Ratings(rating=rating, price=price, placename=placename, text_entry=text_entry)
        db.session.add(rating)
        db.session.commit()

        flash('Rating Added!')

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("FORM SUBMISSION FAILED. PLEASE CORRECT AND RE-SUBMIT" + str(errors))

    return render_template('rating_form.html',form=form)


@app.route('/reviews')
@login_required
def all_ratings():
    rating = Ratings.query.all()
    return render_template('reviews.html', rating=rating)

@app.route('/see_ratings', methods=["GET", "POST"])
@login_required
def ratings():
    rating = Ratings.query.all()
    num = len(rating)
    return render_template('all_ratings.html', rating = rating, num = num)


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!


if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual
