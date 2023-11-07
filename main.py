import datetime
import pathlib
import dateutil.tz
from flask_login import current_user, login_required
from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    request,
    url_for,
    abort,
)
from . import model, db

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    followers = db.aliased(model.User)
    query = (
        db.select(model.Message)
        .join(model.User)
        .join(followers, model.User.followers)
        .where(followers.id == current_user.id)
        .where(model.Message.response_to == None)
        .order_by(model.Message.timestamp.desc())
        .limit(10)
    )
    posts = db.session.execute(query).scalars().all()
    return render_template("main/index.html", posts=posts)


@bp.route("/user/<int:user_id>")
@login_required
def user(user_id):
    user = db.get_or_404(model.User, user_id)
    query = (
        db.select(model.Message)
        .filter_by(user_id=user_id, response_to_id=None)
        .order_by(model.Message.timestamp.desc())
    )
    user_posts = db.session.execute(query).scalars().all()

    follow = "none"
    if current_user.id == user.id:
        follow = "none"
    elif current_user not in user.followers:
        follow = "follow"
    elif current_user in user.followers:
        follow = "unfollow"
    else:
        follow = "none"

    return render_template(
        "main/user.html", user=user, posts=user_posts, follow_button=follow
    )


@bp.route("/post/<int:message_id>")
@login_required
def post(message_id):
    message = db.get_or_404(model.Message, message_id)
    if message.response_to_id != None:
        abort(403, "Forbidden action")
    # if not message:
    #     abort(404, "Post id {} doesn't exist.".format(message_id))
    query = (
        db.select(model.Message)
        .filter_by(response_to_id=message_id)
        .order_by(model.Message.timestamp.desc())
    )
    answers = db.session.execute(query).scalars().all()
    return render_template("main/post.html", post=message, posts=answers)


@bp.route("/new_post")
@login_required
def new_post():
    return render_template("main/new_post.html")


@bp.route("/new_post", methods=["POST"])
@login_required
def new_post_post():
    text = request.form.get("text")
    response_to_id = request.form.get("response_to")
    message = model.Message(
        text=text,
        user=current_user,
        timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
        response_to_id=response_to_id,
    )
    if response_to_id != None:
        db.get_or_404(model.Message, response_to_id)
    db.session.add(message)
    db.session.commit()
    return (
        redirect(url_for("main.post", message_id=message.response_to_id))
        if response_to_id != None
        else redirect(url_for("main.post", message_id=message.id))
    )


@bp.route("/new_photo", methods=["POST"])
@login_required
def new_photo_post():
    recipe_id = request.form.get("recipe_id")

    if recipe_id == None:
        abort(400, f"Please provide a recipe ID")

    uploaded_file = request.files["photo"]

    if uploaded_file.filename != "":
        abort(400, f"Please upload a media file")

    content_type = uploaded_file.content_type
    if content_type == "image/png":
        file_extension = "png"
    elif content_type == "image/jpeg":
        file_extension = "jpg"
    else:
        abort(400, f"Unsupported file type {content_type}")

    recipe = db.get_or_404(model.Recipe, recipe_id)
    photo = model.Photo(user=current_user, recipe=recipe, file_extension=file_extension)
    db.session.add(photo)
    db.session.commit()

    path = (
        pathlib.Path(current_app.root_path)
        / "static"
        / "photos"
        / f"photo-{photo.id}.{file_extension}"
    )
    uploaded_file.save(path)

    return (
        redirect(
            url_for("main.post", recipe_id=recipe_id)
        )  # TODO: change depending on our structure
        if recipe_id != None
        else redirect(url_for("main.post", recipe_id=recipe_id))
    )


@bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    user = db.get_or_404(model.User, user_id)
    if current_user in user.followers or current_user.id == user_id:
        abort(403, "Forbidden action")

    user.followers.append(current_user)
    db.session.commit()

    return redirect(url_for("main.user", user_id=user_id))


@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    user = db.get_or_404(model.User, user_id)
    if current_user not in user.followers or current_user.id == user_id:
        abort(403, "Forbidden action")

    user.followers.remove(current_user)
    db.session.commit()

    return redirect(url_for("main.user", user_id=user_id))
