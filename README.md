# web-apps-project

## Environment variables:
DB_USER=<user>
DB_NAME=<dbname>
DB_PASS=<pw>
DB_HOST=<host>

## Activate virtual environment:
```. venv/bin/activate```

## Connect to the database:
```mysql -h localhost -u cookapp -D cookapp -p```

## Command to create database tables
```from __name__ import db, create_app
app=create_app()
with app.app_context():
    db.create_all()```

## Guide for Installing "mysqlclient" dependency
```# Assume you are activating Python 3 venv
$ brew install mysql-client pkg-config
$ export PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig"
$ pip install mysqlclient```
Source: https://pypi.org/project/mysqlclient/