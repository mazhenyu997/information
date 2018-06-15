import logging

from flask import Flask, session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app
from info import db, models

app = create_app('develop')

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
