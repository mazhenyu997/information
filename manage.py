import logging

from flask import Flask, session, current_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app
from info import db, models
from info.models import User

app = create_app('develop')

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(name, password):
    if not all([name, password]):
        print("参数不足")

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        print(e)

    print("添加成功")


if __name__ == '__main__':
    manager.run()
