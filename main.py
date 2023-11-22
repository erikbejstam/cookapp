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


@bp.route("/new_recipe")
@login_required
def new_recipe():
    return render_template("main/new_recipe.html")


@bp.route("/new_recipe", methods=["POST"])
@login_required
def new_recipe_post():
    recipe_name = request.form.get("recipe_name")
    recipe_description = request.form.get("recipe_description")
    recipe_persons = request.form.get("recipe_persons")
    recipe_time = request.form.get("recipe_time")

    recipe = model.Recipe(
        title=recipe_name,
        description=recipe_description,
        persons=recipe_persons,
        estimated_time=recipe_time,
        user=current_user,
    )

    db.session.add(recipe)
    db.session.commit()

    recipe_photo = request.files.get("recipe_photo")
    store_photo(recipe_photo, recipe_id=recipe.id)

    ingredient_names = request.form.getlist("ingredient_name[]")
    ingredient_quantities = request.form.getlist("ingredient_quantity[]")
    ingredient_units = request.form.getlist("ingredient_unit[]")
    print(ingredient_names)
    ingredients = zip(ingredient_names, ingredient_quantities, ingredient_units)

    for ingredient_name, ingredient_quantity, ingredient_unit in ingredients:
        if not ingredient_name or not ingredient_quantity:
            abort(400, f"Please provide an ingredient")
        ingredient = model.Ingredient(name=ingredient_name)
        db.session.add(ingredient)
        db.session.commit()

        q_ingredient = model.Q_ingredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            amount=ingredient_quantity,
            unit=ingredient_unit,
        )
        db.session.add(q_ingredient)
        db.session.commit()

    step_orders = request.form.getlist("step_order[]")
    step_photos = request.files.getlist("step_photo[]")
    step_texts = request.form.getlist("step_text[]")
    print(step_texts)
    steps = zip(step_orders, step_photos, step_texts)
    print(steps)
    
    for step_order, step_photo, step_text in steps:
        if not step_text or not step_order:
            abort(400, f"Please provide a step")
        step = model.Step(order=step_order, text=step_text, recipe_id=recipe.id)
        db.session.add(step)
        db.session.commit()
        store_photo(step_photo, step_id=step.id)

    return redirect(url_for("main.index"))


def store_photo(uploaded_file, recipe_id=None, step_id=None):
    if not uploaded_file:
        abort(400, f"Please upload a media file")

    content_type = uploaded_file.content_type
    if content_type == "image/png":
        file_extension = "png"
    elif content_type == "image/jpeg":
        file_extension = "jpg"
    else:
        abort(400, f"Unsupported file type {content_type}")

    photo = model.Photo(
        user=current_user,
        recipe_id=recipe_id,
        step_id=step_id,
        file_extension=file_extension,
    )
    db.session.add(photo)
    db.session.commit()

    path = (
        pathlib.Path(current_app.root_path)
        / "static"
        / "photos"
        / f"photo-{photo.id}.{file_extension}"
    )
    uploaded_file.save(path)
    return photo


@bp.route("/new_photo", methods=["POST"])
@login_required
def new_photo_post():
    recipe_id = request.form.get("recipe_id")
    step_id = request.form.get("step_id")

    if recipe_id == None and step_id == None:
        abort(400, f"Please provide to what the picture refers to")

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

    recipe = db.get_or_404(model.Recipe, recipe_id) if recipe_id != None else None
    step = db.get_or_404(model.Step, step_id) if step_id != None else None
    photo = model.Photo(
        user=current_user, recipe=recipe, step=step, file_extension=file_extension
    )
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
        redirect(url_for("main.index"))  # TODO: change depending on our structure
        if recipe_id != None
        else redirect(url_for("main.index"))
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

@bp.route("/create_bookmark/<int:recipe_id>")
@login_required
def create_bookmark(recipe_id):
    
    current_user.bookmarks.append(recipe)
    return redirect(url_for("main.bookmarks"))

@bp.route("/bookmarks/<int:user_id>")
@login_required
def bookmarks(user_id):
    user = db.get_or_404(model.User, user_id)
    if current_user.id != user_id:
        abort(403, "Forbidden action")

    query = db.select(model.Bookmark).where(user.id == user_id)
    bookmarks = db.session.execute(query).scalars().all()

    return render_template("main/bookmarks.html", bookmarks=bookmarks)

@bp.route("/recipe/<int:recipe_id>")
def recipe(recipe_id):
    recipe = db.get_or_404(model.Recipe, recipe_id)

    return render_template("main/recipe.html", recipe=recipe)