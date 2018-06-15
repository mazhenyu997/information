
from flask import render_template
from flask import current_app

from info.models import User
from . import index_blu
from flask import session
from manage import app


@index_blu.route('/')
def hello_world():

    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)

        except Exception as e:
            current_app.logger.error(e)

    data = {
        "user": user.to_dict() if user else None
    }
    return render_template("news/index.html", data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return app.send_static_file('news/favicon.ico')
