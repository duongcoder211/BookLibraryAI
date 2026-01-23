# pip install -U Flask-SQLAlchemy

from flask import Flask, render_template, flash, redirect, url_for, jsonify, request, session
# from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy import select
from db.base import db
import re
from models.user import User
from models.book import Book
from models.userbook import UserBook
import json
import os
from flask_migrate import Migrate
from utils.read_json import book_data_list
# import secrets

from agents.react_agent import ReActAgent
from tools import rag_query_tool, search_web_tool

# Создание агента
# react_agent = ReActAgent()

from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["CHAT_GPT_TOKEN"],
)

def chat_llm(ques):
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b:groq",
        messages=[
            {
                "role": "user",
                "content": f"{ques}"
            }
        ],
    )
    return completion.choices[0].message.content

# create the app
app = Flask(__name__)
# app.secret_key = secrets.token_hex(32)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///booklibrary.db"

# initialize the app with the extension
db.init_app(app)

migrate = Migrate(app=app, db=db)

# db = SQLAlchemy(app=app)
    
# user_book_m2m = db.Table(
#     "user_book",
#     sa.Column("user_id", sa.ForeignKey(User.id), primary_key=True),
#     sa.Column("book_id", sa.ForeignKey(Book.id), primary_key=True),
# )

# Context processor - run before template render
@app.context_processor
def inject_user():
    try:
        # if session.get('user_id'):
        if "user_id" in session.keys():
            return dict(active_user_id=session.get('user_id'))
        else:
            return dict(active_user_id=None)
    except Exception as E:
        print("Error {E} occurred in func inject_user")

@app.route("/")
def load_root():
    users = db.session.execute(db.select(User).order_by(User.id)).scalars().all()
    active_user_id = session.get("user_id") if ("user_id" in session.keys()) else None
    # active_user_id = session.get("user_id") if session.get("user_id") else None => Error: session not has key "user_id"
    return render_template("home.html", users = users, active_user_id=active_user_id)

@app.route("/ask", methods=["POST"])
def answer():
    if request.method == "POST":
        # if "message" in request.json: OR
        if "message" in request.get_json():
            question = request.get_json()["message"]
            # Пример использования
            # result = await react_agent.ask(question) // ask is not async function, so cant use await
            result = chat_llm(ques=question)
            # result = react_agent.ask(question)
            return jsonify({"response": result})

@app.route("/user/<string:name>")
def load_user(name):
    return render_template("user/user.html", name=name.title())

@app.route("/users", methods=["POST", "GET"])
def load_user_list():
    users = db.session.execute(db.select(User).order_by(User.name)).scalars()
    active_user_id = session.get("user_id") if ("user_id" in session.keys()) else None
    return render_template("user/list.html", users=enumerate(users, 1), active_user_id=active_user_id)

@app.route("/user/<int:id>/create")
def create_user(id):
    user = db.get_or_404(User, id)
    return render_template("user/detail.html", user=user)

@app.route("/user/<int:id>/detail")
def user_detail(id):
    # user = db.get_or_404(User, id, description=f"User with Id {id} not found!")
    user = User.query.get(id)
    if user is None:
        return render_template("user/detail.html", message=f"User with Id {id} was not found!")
    return render_template("user/detail.html", user=user)

@app.route("/user/<int:id>/update", methods=["POST", "GET"])
def update_user(id):
    if request.method == "POST":
        try:
            # user = db.get_or_404(User, id)
            if ("user_id" in session.keys()):
                if session["user_id"] == id: #postman
                    user = User.query.get(id)

                    name = request.form["name"]
                    email = request.form["email"]

                    user.modify_infor(name, email)
                    return redirect(f"/users")
                
            return redirect('/login')
        # except sa.exc.IntegrityError as IE:
        except Exception as E:
            db.session.rollback()
            flash(f"{E}", "danger")
            return redirect(f"/user/{id}/update")
    
    elif "user_id" in session.keys():
        if session["user_id"] == id:
            user = User.query.get(id)
            return render_template("user/update.html", user=user)
        else:
            flash("That page does not exist!", "danger")
            return redirect(f"/user/{session["user_id"]}/update")
    
    elif "user_id" not in session.keys():
        flash("That page does not exist!", "danger")
        return redirect("/users")
    
    flash("That page does not exist!", "danger")
    return redirect(f"/user/{session["user_id"]}/update")

@app.route("/user/<int:id>/delete")
def delete_user(id):
    if "user_id" in session.keys():
        user = db.get_or_404(User, id)
        
        if user.id != session["user_id"]:
            return render_template("404_error.html")
            # return redirect("/users")

        try:
            if user.user_books:
                user.remove_all_from_archive()
            db.session.delete(user)
            db.session.commit()
            return redirect("/users")
        except Exception as E:
            flash("That page does not exist!", "danger")
            return redirect("/users")
    
    return redirect('/login')

@app.route("/user/<int:id>/archive")
def load_user_archive(id):
    try:
        if session['user_id'] == id:
            # user = db.get_or_404(User, id)
            user = User.query.get(id)
            if user.user_books:
                userbooks = user.user_books
                return render_template("user/archive.html",  userbooks = enumerate(userbooks, 1))
            # return redirect(url_for("load_root"))
            return render_template("user/archive.html",  userbooks=None, message="You dont have any book in your archive!")
        # return render_template("404_error.html")
        raise ValueError("Error from func load_user_archive!")
    except Exception as E:
        # print(E)
        try:
            flash("That page does not exist!", "danger")
            return redirect(f'/user/{session['user_id']}/archive')
        except Exception as E:
            return redirect(f'/login')
            
        # return render_template("404_error.html")
    
@app.route("/user/<int:user_id>/archive/book/<int:book_id>/add")
def add_user_book(user_id, book_id):
    try:
        user = User.query.get(user_id)
        if user_id != session["user_id"]:
            raise ValueError
        user.add_to_archive(book_id)
        return redirect(f"/books")
    except Exception:
        return render_template("404_error.html")

@app.route("/user/<int:user_id>/archive/book/<int:book_id>/remove")
def remove_user_book(user_id, book_id):
    try:
        # user = db.get_or_404(User, id)
        if "user_id" in session.keys():
            user = User.query.get(user_id)
            if user_id != session["user_id"]:
                raise ValueError
            user.remove_from_archive(book_id)
            flash("Book was removed successfully!", "success")
            return redirect(f"/user/{user_id}/archive")
        return redirect("/login")
    except Exception:
        return render_template("404_error.html")
    
@app.route("/user/<int:user_id>/archive/book/<int:book_id>/status/update")
def set_status_user_book(user_id, book_id):

    try:
        if "user_id" in session.keys():
            if user_id != session["user_id"]:
                raise ValueError
            
            user = User.query.get(user_id)
            user.update_reading_status(book_id)
            return redirect(f"/user/{user_id}/archive")
        
        return redirect("/login")
    except Exception as E:
        return render_template("404_error.html")
    
@app.route("/books")
def load_book_list():
    books = db.session.execute(db.select(Book).order_by(Book.name)).scalars().all()
    try:
        # user = User.query.get(session.get('user_id')) # will raise an error in future because user_id is not finded in session
        # if user:
        if "user_id" in session.keys():
            user = User.query.get(session.get('user_id'))
            user_books = [user_book.book_id for user_book in user.user_books]
        else:
            user_books=[]
        return render_template("book/list.html", books = books, user_books = user_books)
    except Exception as E:
        print(f"Error: {E} occurred in func load_book_list!")
        return render_template("book/list.html", books = books)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        try:
            username_or_email = request.form["username"]
            password = request.form["password"]

            # if db.session.execute(db.select(User).filter(User.username == username_or_email)).scalar() == None\
            #     and(,) db.session.execute(db.select(User).filter(User.email == username_or_email)).scalar() == None:
            # if db.session.execute(db.select(User).filter((User.username == username_or_email) and(,) or(|) (User.email == username_or_email))).scalar() == None:
            #     print("Username was not registed")
            #     return "Username was not registed"

            # if db.session.execute(db.select(User).filter(User.username == username_or_email).filter(User.password == password)).scalar() == None\
            #     and db.session.execute(db.select(User).filter(User.email == username_or_email).filter(User.password == password)).scalar() == None:
            #         print("Password is incorrect")
            #         return "Password is incorrect"

            user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

            if user is None:
                flash("Login informations are incorrect", "danger")
                return redirect(url_for("login"))
            
            if user.password != password: #Have to check password hash
                flash("Login informations are incorrect", "danger")
                return redirect(url_for("login"))
            
            session['user_id'] = user.id
            session['user_name'] = user.name

            flash(f"Logged in successfully! Welcome {session['user_name'] } to website <(^_^)>", "success")

            return redirect(url_for("load_root"))
        except Exception as E:
            message = f"Login error: {E}"
            flash(message, "danger")
            return redirect(url_for("login"))
    return render_template("auth/login.html")
    # return render_template("authorization/login.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    try:
        session.clear()
        # print(session.items())

        flash("Logged out successfully! See you again! :-(", "info")
        return redirect(url_for("load_root"))
    except Exception as E:
        print(f"Error {E} occured in func logout")
        return redirect(url_for("load_root"))
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            confirm_password = request.form["confirm-password"]

            # print(request.form.to_dict())

            if request.form.getlist("rememberme"): # get value checkbox input -> [] if not, ['on'] if has
                print(request.form.getlist("rememberme")[0])

            if db.session.execute(db.select(User).filter(User.username == username)).scalar():
                raise ValueError("This username exists")

            if db.session.execute(db.select(User).filter(User.email == email)).scalar():
                raise ValueError("This email exists")
            
            if password != confirm_password:
                raise ValueError("Confirm password is not correct")
            
            user_infor_form = request.form.to_dict()
            user_infor_form["name"] = "user" + str(abs(username.__hash__()%(10**6)))
            user_infor = {key: value for key, value in user_infor_form.items() if key in ["name", "email", "username", "password"]}

            new_user = User(**user_infor)
            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id

            flash("Created account successfully! Now you can use service! <(^_^)>", "success")
            return redirect("/")
        except Exception as E:
            message = f"Register error: {E}"
            flash(message, "danger")
            return redirect(url_for("register"))
    return render_template("auth/register.html")
    # return render_template("authorization/register.html")

@app.route("/.well-known/appspecific/com.chrome.devtools.json", methods=["GET"])
def use_devtools():
    return render_template("user/user.html", user="Developer")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404_error.html'), 404

# @app.route("/users/create", methods=["GET", "POST"])
# def user_create():
#     if request.method == "POST":
#         user = User(
#             username=request.form["username"],
#             email=request.form["email"],
#         )
#         db.session.add(user)
#         db.session.commit()
#         return redirect(url_for("user_detail", id=user.id))

#     return render_template("user/create.html")

with app.app_context():
    user_infors = [{"name": "user1", "email": "email1@gmail.com", "username": "username1", "password": "password1"},
                {"name": "user2", "email": "email2@gmail.com", "username": "username2", "password": "password2"},
                {"name": "user3", "email": "email3@gmail.com", "username": "username3", "password": "password3"},
                {"name": "user4", "email": "email4@gmail.com", "username": "username4", "password": "password4"},
                {"name": "user5", "email": "email5@gmail.com", "username": "username5", "password": "password5"},
                ]
    
    # book_infors = [{"name": "book1", "author": "author1", "category": "category1", "describe": "describe1", "publication_date": "10.11.2025"},
    #             {"name": "book2", "author": "author2", "category": "category2", "describe": "describe2", "publication_date": "11.11.2025"},
    #             {"name": "book3", "author": "author3", "category": "category3", "describe": "describe3", "publication_date": "12.11.2025"},
    #             {"name": "book4", "author": "author4", "category": "category4", "describe": "describe4", "publication_date": "13.11.2025"},
    #             {"name": "book5", "author": "author5", "category": "category5", "describe": "describe5", "publication_date": "14.11.2025"},
    #             ]
    book_infors = book_data_list

    try:
        db.drop_all()

        db.create_all()

        for user_inf in user_infors:
            db.session.add(User(**user_inf))
            db.session.flush()

        for book_inf in book_infors:
            db.session.add(Book(**book_inf))
            db.session.flush()
        
        # AttributeError: 'Select' object has no attribute 'name'
        # user1 = select(User).where(User.id == 1)

        # .filter(expression) # filter by condition
        # .filter_by(assignment) # filter by condition
        # .order_by() # arrange by column

        user1 = db.session.execute(db.select(User).filter_by(id = 1)).scalar()
        user1 = db.session.execute(db.select(User).filter(User.id == 1)).scalar()
        user2 = db.session.execute(db.select(User).filter(User.id == 2)).scalar()
        user3 = db.session.execute(db.select(User).filter(User.id == 3)).scalar()
        books = db.session.execute(db.select(Book).order_by(Book.name)).scalars().all()

        db.session.add(UserBook(user=user1, book=books[1], reading_status = "completed"))
        db.session.add(UserBook(user=user1, book=books[2]))

        db.session.add(UserBook(user=user2, book=books[1]))
        db.session.add(UserBook(user=user2, book=books[3], reading_status = "reading"))

        db.session.add(UserBook(user=user3, book=books[1]))
        db.session.add(UserBook(user=user3, book=books[2]))
        db.session.add(UserBook(user=user3, book=books[3]))

        db.session.commit()

    except sa.exc.IntegrityError as IE:
        print(f"Error occurred!: {IE}")

# if __name__ == "__main__":
#     app.run("0.0.0.0", 5555)