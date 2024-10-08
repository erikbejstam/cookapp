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
from sqlalchemy import func
from . import model, db
import re
from sqlalchemy import func

bp = Blueprint("main", __name__)


def get_user_vote(recipe_id, user_id):
    return (
        db.session.execute(
            db.select(model.Rating.value)
            .where(model.Rating.user_id == user_id)
            .where(model.Rating.recipe_id == recipe_id)
        ).scalar_one_or_none()
        or 0
    )


def get_user_bookmark(recipe_id, user_id):
    return (
        db.session.execute(
            db.select(model.Bookmark)
            .where(model.Bookmark.user_id == user_id)
            .where(model.Bookmark.recipe_id == recipe_id)
        ).scalar_one_or_none()
        or 0
    )


def get_total_rating(recipe_id):
    query = (
        db.select(func.sum(model.Rating.value).label("total_rating"))
        .where(model.Rating.recipe_id == recipe_id)
        .group_by(model.Rating.recipe_id)
    )
    return db.session.execute(query).scalar_one_or_none() or 0


def extract_step_photos(request):
    step_photos = {}
    for key in request.files.keys():
        if key.startswith("step_photo["):
            file = request.files[key]
            if file.filename != "":
                number = re.search(r"\d+", key).group()
                step_photos[number] = file
    return step_photos


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


@bp.route("/")
def index():
    query = (
        db.select(
            model.Rating.recipe_id,
            func.sum(model.Rating.value).label("total_rating"),
        )
        .group_by(model.Rating.recipe_id)
        .order_by(func.sum(model.Rating.value).desc())
        .limit(60)
    )

    result = db.session.execute(query)

    recipes = []
    for row in result:
        recipe = db.get_or_404(model.Recipe, row[0])
        total_rating = row[1]

        user_vote = 0
        user_bookmark = False
        if current_user.is_authenticated:
            current_user_id = current_user.id
            user_vote = get_user_vote(recipe.id, current_user_id)
            user_bookmark = get_user_bookmark(recipe.id, current_user_id)

        recipes.append((recipe, total_rating, user_vote, user_bookmark))

    if len(recipes) < 10:
        number_of_recipes = 10 - len(recipes)
        query = (
            db.select(model.Recipe)
            .outerjoin(model.Rating)
            .where(model.Rating.recipe_id == None)
            .order_by(model.Recipe.timestamp.desc())
            .limit(number_of_recipes)
        )
        rateless_recipes = db.session.execute(query).scalars().all()
        for recipe in rateless_recipes:
            user_vote = 0
            user_bookmark = False
            if current_user.is_authenticated:
                current_user_id = current_user.id
                user_vote = get_user_vote(recipe.id, current_user_id)
                user_bookmark = get_user_bookmark(recipe.id, current_user_id)
            recipes.append((recipe, 0, user_vote, user_bookmark))

    recipes.sort(key=lambda x: x[1], reverse=True)

    return render_template("main/index.html", recipes=recipes)


@bp.route("/user/<int:user_id>")
@login_required
def user(user_id):
    user = db.get_or_404(model.User, user_id)

    query = (
        db.select(
            model.Recipe,
        )
        .where(model.Recipe.user_id == user_id)
        .limit(60)
    )

    result = db.session.execute(query).scalars().all()

    recipes = []
    for recipe in result:
        total_rating = get_total_rating(recipe.id)
        user_vote = 0
        user_bookmark = False
        if current_user.is_authenticated:
            current_user_id = current_user.id
            user_vote = get_user_vote(recipe.id, current_user_id)
            user_bookmark = get_user_bookmark(recipe.id, current_user_id)

        recipes.append((recipe, total_rating, user_vote, user_bookmark))

    recipes.sort(key=lambda x: x[1], reverse=True)

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
        "main/user.html",
        user=user,
        recipes=recipes,
        follow_button=follow,
    )


@bp.route("/rate/<int:recipe_id>", methods=["POST"])
@login_required
def rate(recipe_id):
    value = request.form.get("value")
    if value not in ["-1", "1"]:
        abort(400, "Invalid rating value")

    existing_rating = model.Rating.query.filter_by(
        user_id=current_user.id,
        recipe_id=recipe_id,
    ).first()

    if existing_rating != None:
        db.session.delete(existing_rating)

    if existing_rating == None or existing_rating.value != int(value):
        rating = model.Rating(
            user_id=current_user.id,
            recipe_id=recipe_id,
            value=value,
        )
        db.session.add(rating)

    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@bp.route("/new_photo/<int:recipe_id>", methods=["POST"])
@login_required
def new_photo_post(recipe_id):
    if recipe_id == None:
        abort(400, f"Please provide to what the picture refers to")

    db.get_or_404(model.Recipe, recipe_id)

    uploaded_file = request.files["photo"]
    store_photo(uploaded_file, recipe_id=recipe_id)
    return redirect(request.referrer or url_for("main.recipe", recipe_id=recipe_id))


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
        timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
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
    step_texts = request.form.getlist("step_text[]")
    step_photos = extract_step_photos(request)

    steps = zip(step_orders, step_texts)

    current_step = 0
    for step_order, step_text in steps:
        if not step_text or not step_order:
            abort(400, f"Please provide a step")
        step = model.Step(order=step_order, text=step_text, recipe_id=recipe.id)
        db.session.add(step)
        db.session.commit()

        if str(current_step) in step_photos.keys():
            step_photo = step_photos[str(current_step)]
            store_photo(step_photo, step_id=step.id)
        current_step += 1

    return redirect(url_for("main.index"))


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


@bp.route("/create_bookmark/<int:recipe_id>", methods=["POST"])
@login_required
def create_bookmark(recipe_id):
    bookmark_exists = False
    for bookmark in current_user.bookmarks:
        if bookmark.recipe_id == recipe_id:
            db.session.delete(bookmark)
            bookmark_exists = True
            break

    if not bookmark_exists:
        bookmark = model.Bookmark(
            user_id=current_user.id,
            recipe_id=recipe_id,
        )
        db.session.add(bookmark)

    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@bp.route("/remove_bookmark/<int:bookmark_id>", methods=["POST"])
@login_required
def remove_bookmark(bookmark_id):
    bookmark = db.get_or_404(model.Bookmark, bookmark_id)
    db.session.delete(bookmark)
    db.session.commit()
    return redirect(url_for("main.bookmarks", user_id=current_user.id))


@bp.route("/bookmarks/<int:user_id>")
@login_required
def bookmarks(user_id):
    db.get_or_404(model.User, user_id)
    if current_user.id != user_id:
        abort(403, "Forbidden action")
    query = db.select(
        model.Bookmark.recipe_id,
    ).where(model.Bookmark.user_id == user_id)

    result = db.session.execute(query)

    recipes = []
    for row in result:
        recipe = db.get_or_404(model.Recipe, row.recipe_id)
        total_rating = get_total_rating(recipe.id)
        user_vote = get_user_vote(recipe.id, user_id)
        user_bookmark = get_user_bookmark(recipe.id, user_id)
        recipes.append((recipe, total_rating, user_vote, user_bookmark))

    recipes.sort(key=lambda x: x[1], reverse=True)
    return render_template("main/bookmarks.html", recipes=recipes)


@bp.route("/recipe/<int:recipe_id>")
def recipe(recipe_id):
    recipe = db.get_or_404(model.Recipe, recipe_id)

    total_rating = get_total_rating(recipe.id)
    user_vote = 0
    user_bookmark = False
    if current_user.is_authenticated:
        current_user_id = current_user.id
        user_vote = get_user_vote(recipe.id, current_user_id)
        user_bookmark = get_user_bookmark(recipe.id, current_user_id)

    return render_template(
        "main/recipe.html", recipe=(recipe, total_rating, user_vote, user_bookmark)
    )

