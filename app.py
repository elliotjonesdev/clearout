"""This file manages items and categories with user registration
and login functionality"""

import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# Check for environment variables in an env.py file
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

# Configure MongoDB connection using environment variables
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_item")
def get_item():
    """Route to display a list of items."""
    item = list(mongo.db.tasks.find())
    return render_template("item.html", item=item)


@app.route("/search", methods=["GET", "POST"])
def search():
    """Route to search for items based on user input."""
    query = request.form.get("query")
    item = list(mongo.db.tasks.find({"$text": {"$search": query}}))
    return render_template("item.html", item=item)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Route to handle user registration."""
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # puts the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Route to handle user login."""
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome Back, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """Route to display user profiles."""
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Route to log out the user."""
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    """Route to add new items."""
    if request.method == "POST":
        is_sold = "on" if request.form.get("is_sold") else "off"
        item = {
            "category_name": request.form.get("category_name"),
            "item_name": request.form.get("item_name"),
            "item_description": request.form.get("item_description"),
            "item_delivery": request.form.get("item_delivery"),
            "item_image": request.form.get("item_image"),
            "item_location": request.form.get("item_location"),
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(item)
        flash("Item Successfully Added")
        return redirect(url_for("get_item"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_item.html", categories=categories)


@app.route("/edit_item/<item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    """Route to edit existing items."""
    if request.method == "POST":
        is_sold = "on" if request.form.get("is_sold") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "item_name": request.form.get("item_name"),
            "item_description": request.form.get("item_description"),
            "item_delivery": request.form.get("item_delivery"),
            "item_image": request.form.get("item_image"),
            "item_location": request.form.get("item_location"),
            "created_by": session["user"]
        }
        mongo.db.tasks.update_one({"_id": ObjectId(item_id)}, {"$set": submit})
        flash("Item Successfully Updated")

    item = mongo.db.tasks.find_one({"_id": ObjectId(item_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_item.html", item=item, categories=categories)


@app.route("/delete_item/<item_id>")
def delete_item(item_id):
    """Route to delete items."""
    mongo.db.tasks.delete_one({"_id": ObjectId(item_id)})
    flash("Item Successfully Deleted")
    return redirect(url_for("get_item"))


@app.route("/get_categories")
def get_categories():
    """Route to display a list of categories."""
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    """Route to add new categories."""
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    """Route to edit existing categories."""
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    """Route to delete categories."""
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)