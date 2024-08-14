
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'yeet'
db = SQLAlchemy(app)
bc = Bcrypt(app)
app.app_context().push()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Matches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match = db.Column(db.String(100),nullable=False)
    date = db.Column(db.String(20),nullable=False)
    promotion = db.Column(db.String(40),nullable=False)
    match_type = db.Column(db.String(30),nullable=False)
    event = db.Column(db.String(30),nullable=False)
    par1 = db.Column(db.String(30),nullable=False)
    par2 = db.Column(db.String(30),nullable=False)
    par3 = db.Column(db.String(30),nullable=True)
    par4 = db.Column(db.String(30),nullable=True)
    par5 = db.Column(db.String(30),nullable=True)
    par6 = db.Column(db.String(30),nullable=True)
    par7 = db.Column(db.String(30),nullable=True)
    par8 = db.Column(db.String(30),nullable=True)

class Ratings(db.Model):
    rating_index = db.Column(db.Integer,primary_key=True)
    user_index = db.Column(db.Integer)
    match_index = db.Column(db.Integer)
    rating = db.Column(db.Integer)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(),Length(min=3,max=20)],render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(),Length(min=5,max=20)],render_kw={"placeholder":"Password"})
    submit = SubmitField("Register")

    def validate_username(self,username):
        existing = User.query.filter_by(username=username.data).first()
        if existing:
            raise ValidationError("That username already exists. Please select another.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(),Length(min=3,max=20)],render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(),Length(min=5,max=20)],render_kw={"placeholder":"Password"})
    submit = SubmitField("Login")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from helper import get_recent_matches, get_user_distribution, make_user_distribution_hist
@app.route("/")
def home():
    last_date = Matches.query.order_by(Matches.date.desc()).limit(1).all()[0].date
    updates = get_recent_matches(last_date,[1,7,2287])
    all_matches = Matches.query.all()
    for i in updates:
        if (i[0] not in [m.match for m in all_matches]) or (not Matches.query.filter_by(match=i[0],date=i[1]).first()):
            match = Matches(
                id=Matches.query.count(),
                match=i[0],
                date=i[1],
                promotion=i[2],
                match_type=i[3],
                event=i[4],
                par1=i[5],par2=i[6],par3=i[7],par4=i[8],par5=i[9],par6=i[10],par7=i[11],par8=i[12]
                )
            db.session.add(match)
    db.session.commit()
    ye = [x for x in Matches.query.order_by(Matches.date.desc()).limit(25).all()]
    return render_template("home.html",matches=[{"Fixture:": i.match, "Date:":i.date,"Event:":i.event} for i in ye])

@app.route("/about",methods=['POST','GET'])
def about():
    return render_template("about.html")


@app.route("/login",methods=['POST','GET'])
def login():
    global form
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bc.check_password_hash(user.password,form.password.data):
                login_user(user)
                session["id"] = user.id
                session["username"] = user.username
                q = [x for x in Ratings.query.filter_by(user_index=user.id)]
                matches = []
                for i in q:
                    matches.append(Matches.query.get(i.match_index))
                return redirect(url_for("user_home"))
    return render_template("login.html",form=form)

@app.route("/logout",methods=['POST','GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/register",methods=['POST','GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = bc.generate_password_hash(form.password.data)
        user = User()
        user.username = form.username.data
        user.password = hashed
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html",form=form)

@app.route("/input",methods=['POST','GET'])
def input_new_match():
    user = User.query.filter_by(username=session["username"]).first()
    if request.method == "POST":
        match = Ratings()
        match.rating = request.form['rating']
        match.match_index = request.form['selected_match_id']
        match.user_index = current_user.id
        dist = get_user_distribution(current_user.id)
        if int(match.match_index) not in [x.match_index for x in Ratings.query.filter_by(user_index=session["id"]).all()]:
            db.session.add(match)
            db.session.commit()
        else:
            print("Sorry, match is already inputted")
            return render_template("input.html",again=True)
        q = [x for x in Ratings.query.filter_by(user_index=user.id)]
        matches = []
        for i in q:
            matches.append(Matches.query.get(i.match_index))
        matches = reversed(matches)
        q = reversed(q)
        total = sum([dist[x][0] for x in dist])
        sorted_ratings = sorted([x.rating for x in q])
        return redirect(url_for('user_home'))
    else:
        return render_template("input.html")

@app.route('/get_matches')
def get_matches():
    input_text = request.args.get('input')
    matches = Matches.query.filter(Matches.match.ilike(f'%{input_text}%')).all()
    return jsonify([{'name': m.match,'date':m.date,'event':m.event,'id':m.id} for m in matches])
@app.route("/user_home",methods=['POST','GET'])
@login_required
def user_home():
    if request.method=="POST":
        return render_template("input.html")
    else:
        plot_url = make_user_distribution_hist(current_user.id)
        dist = get_user_distribution(current_user.id)
        user = User.query.filter_by(username=session["username"]).first()
        q = [x for x in Ratings.query.filter_by(user_index=user.id)]
        matches = []
        for i in q:
            matches.append(Matches.query.get(i.match_index))
        total = sum([dist[x][0] for x in dist])
        sorted_ratings = sorted([x.rating for x in q])
        matches,q = reversed(matches),reversed(q)
        if total == 0:
            mean = 0
        else:
            mean = sum([dist[x][1] for x in dist])/total
        return render_template("user_home.html", username=session["username"], id = str(current_user.id),
                               matches=zip(matches, q),dist=dist,total=total, mean=mean,
                               median = np.median(sorted_ratings), std = np.std(sorted_ratings),total_matches=len(sorted_ratings),
                               plot = plot_url)
@app.route("/superstar_dist",methods=['POST','GET'])
def view_dist():
    if request.method == 'POST':
        return render_template("user_home.html")
    else:
        dist = get_user_distribution(current_user.id)
        return render_template("by_superstar.html",dist = dist,total=sum([dist[x][0] for x in dist]))

@app.route("/delete_match/<int:match_id>",methods=['POST','GET'])
def delete_match(match_id):
    if request.method == 'POST':
        user = current_user.id
        if user:
            Ratings.query.filter_by(match_index=int(match_id), user_index=user).delete()
            db.session.commit()
            return redirect(url_for('user_home'))
        else:
            return "User not found", 404