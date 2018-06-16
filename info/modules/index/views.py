
from flask import render_template, request, jsonify
from flask import current_app

from info.models import User, News
from info.utils.response_code import RET
from . import index_blu
from flask import session
from manage import app


@index_blu.route('/news_list')
def news_list():
    # 新闻分类cid
    try:

        cid = int(request.args.get("cid", "1"))
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "10"))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    filters = []
    if cid != 1:  # 不查询最新的数据
        filters.append(News.category_id == cid)
    try:
        news_data = News.query.filter(*filters).order_by(News.create_time.desc())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    paginate = news_data.paginate(page, per_page, False)
    news_list_data = paginate.items
    total_page = paginate.pages
    cur_page = paginate.page

    # 模型对象转成字典列表
    news_dict_list = []
    for news in news_list_data:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "total_page":total_page,
        "current_page":cur_page,
        "news_dict_li":news_dict_list
    }

    return jsonify(errno=RET.OK, errmsg="ok", data=data)


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
