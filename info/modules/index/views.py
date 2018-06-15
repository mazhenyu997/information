
from flask import render_template
from flask import current_app

from info.models import User, News
from . import index_blu
from flask import session
from manage import app


@index_blu.route('/')
def index():

    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)

        except Exception as e:
            current_app.logger.error(e)
    # 右侧新闻的逻辑
    news_right_list = []
    try:
        news_right_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    # 将列表中的对象转为列表中的字典
    news_dict_list = []
    for news in news_right_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_list
    }
    return render_template("news/index.html", data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return app.send_static_file('news/favicon.ico')
