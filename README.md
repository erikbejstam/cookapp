# Cookapp
Taste and Share 

- Erik Kiessig 100518034
- Min Jegal 100517384
- Erik Bejstam 100518211

## How to get started:
Name of flask app: cookapp
Signup: 
- can be found via login button and with trying to bookmark or vote
- /signup
- to access[User view] press your username

## Additional features:

[Main View]
- Recipe previews that looks nice => includes total rating count, bookmark/up-/downvote buttons
- Up-/downvote buttons indicate whether the user has already voted
- Bookmark button that switches color when recipe is bookmarked
- The website lists the recipes in order of highest rating
- Icons attached to the links to the different views of the website => use of fontawesome
- Plus button for adding a new recipe
- Timestamp added to the recipe class in the model, which is displayed in the recipe preview

[Recipe Creation View]
- When you fill in a step, a form for a new one appears automatically. 
- When you fill in an ingredient, a form for a new one appears.
- No need to delete the unused step and ingredient forms
- Automatic adjustment for the step counter even after deletion of a step.
- Steps can be enriched with an optional image upload. => added image for steps to model
- You can remove ingredients or steps while creating the recipe.

[User View]
- User views can be approached by clicking the user name from the nav bar
- Display number of followers/following
- Follow/unfollow functionality

[Recipe View]
- Users can upload pictures of their masterpiece and they are nicely shown as additional pictures on top
- User's uploaded image is previewed.
- During previewing the users can delete the image of their version of the dish.

[Other]
- When users sign in, they end up in the main view
- If a logged in user tries to login or signup by adding /login or /signup to the url, the user is redirected to the main page.
- Author can be reached from the recipe preview
- Triggering up-/downvote and bookmark keeps the user in the same view

## Environment variables:
```
DB_CONNECTION_URL=mysql+mysqldb://<db_user>:<db_pass>@<db_host>/<db_name>
SECRET_KEY=<key>
```

## Activate virtual environment:
```. venv/bin/activate```

## Connect to the database:
```mysql -h localhost -u cookapp -D cookapp -p```

## Command to create database tables
```
from cookapp import db, create_app 
app=create_app()
with app.app_context():
    db.create_all()
```
```
# Change 'recipes' to your package's name below
from cookapp import db, create_app
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
```

```
from cookapp import db, create_app
from sqlalchemy.sql import text
app = create_app()
with app.app_context():
    db.session.execute(text('SET FOREIGN_KEY_CHECKS=0;'))
    db.session.commit()
    db.drop_all()
    db.session.execute(text('SET FOREIGN_KEY_CHECKS=1;'))
    db.session.commit()
    db.create_all()
```

## Command to run the app
```flask --debug --app=cookapp run```

## Code to debug inside python code
```import pdb; pdb.set_trace()```

## Guide for Installing "mysqlclient" dependency
```
# Assume you are activating Python 3 venv
$ brew install mysql-client pkg-config
$ export PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig"
$ pip install mysqlclient
```
Source: https://pypi.org/project/mysqlclient/