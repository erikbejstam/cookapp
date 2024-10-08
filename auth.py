from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db, bcrypt
import flask_login
from flask_login import current_user


from . import model

bp = Blueprint("auth", __name__)


@bp.route("/signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    else:
        return render_template("auth/signup.html")


@bp.route("/signup", methods=["POST"])
def signup_post():
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    # Check that passwords are equal
    if password != request.form.get("password_repeat"):
        flash("Sorry, passwords are different!")
        return redirect(url_for("auth.signup"))
    # Check if the email is already at the database
    query = db.select(model.User).where(model.User.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    if user:
        flash("Sorry, invalid email! &#128549;")
        return redirect(url_for("auth.signup"))
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = model.User(email=email, name=username, password=password_hash)
    db.session.add(new_user)
    db.session.commit()
    flash("You've successfully signed up! &#128522")
    return redirect(url_for("auth.login"))


@bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    else:
        return render_template("auth/login.html")


@bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    query = db.select(model.User).where(model.User.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    if user and bcrypt.check_password_hash(user.password, password):
        flask_login.login_user(user)
        next_page = request.form.get('next')
        if not next_page or url_for('auth.login') in next_page:
            next_page = url_for("main.index")
        return redirect(next_page)
    else:
        flash("Invalid credentials!")
        return redirect(url_for("auth.login"))


@bp.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for("auth.login"))
