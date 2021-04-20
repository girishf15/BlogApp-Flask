import os
import json
import math

from datetime import datetime

from flask import Flask, request, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'the random string'


with open('config.json', 'r') as config:
    params = json.load(config)['params']

local_server = params["local_server"]
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_server_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_server_uri"]

db = SQLAlchemy(app)


app.config.update(
    MAIL_SERVER = 'smtp.sendgrid.net',
    MAIL_PORT = '587',
    MAIL_USERNAME = params["mail_username"],
    MAIL_PASSWORD = params["mail_password"],
    SENDER = "girishfedram@gmail.com",
    UPLOAD_LOCATION=params["upload_location"]
)

mail = Mail(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():


    number_of_posts = int(params["no_of_posts"])

    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / number_of_posts)

    #pagination logic goes here
    page = request.args.get("page")

    if not str(page).isdigit():
        page = 1
    
    page = int(page)
    
    posts = posts[(page-1) * number_of_posts : ((page-1) * number_of_posts) + number_of_posts]
    
    #first
    if page == 1:
        prev = "#"
        next = "/?page="+str(page+1)

    elif page == last:
        prev = "/?page="+str(page-1)
        next = "#"
    
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if request.method == "POST":

        if 'user' in session and session['user'] == params['admin_username']:
            #user already logged in render directly
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

        username = request.form.get('email')
        password = request.form.get('password')

        print("username, password", username, password)

        if username == params['admin_username'] and password == params["admin_password"]:

            posts = Posts.query.all()

            #user valid
            session['user'] = username
            print("Valid user")
            return render_template('dashboard.html', params=params, posts=posts)

    elif request.method == "GET":

        if 'user' in session and session['user'] == params['admin_username']:
            #user already logged in render directly
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)


@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit_post(sno):

    if 'user' in session and session['user'] == params['admin_username']:

        if request.method == 'POST':

            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            
            if sno=='0':
                post = Posts(title=title, slug=slug, content=content, tagline=tagline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):

    if 'user' in session and session['user'] == params['admin_username']:

        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')

@app.route("/post/<string:post_slug>", methods=["GET"])
def blogposts(post_slug):

    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', post=post)


@app.route("/uploader", methods = ["POST", "GET"])
def uploader():

    if 'user' in session and session['user'] == params['admin_username']:

        if request.method == "POST":

            print("os.path.dirname(__file__)", os.path.dirname(__file__), request.files)

            f = request.files['file']
            f.save(os.path.join(app.config.get("UPLOAD_LOCATION"), secure_filename(f.filename)))

            return "Uploaded Successsfully...........!!"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/contact", methods = ["POST", "GET"])
def contact():

    if request.method=="POST":

        # SAVE TO DB
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()

        # send mail after db operation
        msg = Message(subject="Hello",
                    sender=app.config.get("SENDER"),
                    recipients=["girishfedram007@gmail.com"], # replace with your email for testing
                    body="This is a test email I sent with Gmail and Python!")
        mail.send(msg)
    
    return render_template('contact.html')

app.run(debug=True)