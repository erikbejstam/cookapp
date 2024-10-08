from . import db
import flask_login


class FollowingAssociation(db.Model):
    follower_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )


class User(flask_login.UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    recipes = db.relationship("Recipe", back_populates="user")
    ratings = db.relationship("Rating", back_populates="user")
    photos = db.relationship("Photo", back_populates="user")
    messages = db.relationship("Message", back_populates="user")
    bookmarks = db.relationship("Bookmark", back_populates="user")
    following = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.follower_id == id,
        secondaryjoin=FollowingAssociation.followed_id == id,
        back_populates="followers",
    )
    followers = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.followed_id == id,
        secondaryjoin=FollowingAssociation.follower_id == id,
        back_populates="following",
    )


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False) 
    persons = db.Column(db.Integer, nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="recipes")

    q_ingredients = db.relationship("Q_ingredient", back_populates="recipe")
    photos = db.relationship("Photo", back_populates="recipe")
    steps = db.relationship("Step", back_populates="recipe")
    ratings = db.relationship("Rating", back_populates="recipe")
    bookmarks = db.relationship("Bookmark", back_populates="recipe")


class Q_ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32), nullable=False)

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    recipe = db.relationship("Recipe", back_populates="q_ingredients")
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredient.id"), nullable=False
    )
    ingredient = db.relationship("Ingredient", back_populates="q_ingredients")


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    q_ingredients = db.relationship("Q_ingredient", back_populates="ingredient")


class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    photos = db.relationship("Photo", back_populates="step")

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    recipe = db.relationship("Recipe", back_populates="steps")


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # 0 => downvote, 1 => upvote

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    recipe = db.relationship("Recipe", back_populates="ratings")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="ratings")


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_extension = db.Column(db.String(8), nullable=False)
                                                            
    step_id = db.Column(db.Integer, db.ForeignKey("step.id"), nullable=True)
    step = db.relationship("Step", back_populates="photos")
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=True) 
    recipe = db.relationship("Recipe", back_populates="photos")
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="photos")


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="bookmarks")
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    recipe = db.relationship("Recipe", back_populates="bookmarks")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="messages")
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    response_to_id = db.Column(db.Integer, db.ForeignKey("message.id"))
    response_to = db.relationship(
        "Message", back_populates="responses", remote_side=[id]
    )   
    responses = db.relationship(
        "Message", back_populates="response_to", remote_side=[response_to_id]
    )

    # + alpha ) search function  , lists with the same ingridients
    # link a photo to a steo=p, adding a new column, 
