from datetime import datetime, timedelta
import time

from info.modules.admin import admin_blu
from flask import render_template, request, jsonify, current_app, session, redirect, url_for, g
from info.models import User, News
from info.utils.common import user_login_data
from info.utils.response_code import RET




@admin_blu.route('/index')
@user_login_data
def index():
    user = g.user
    data = {
        "user": user.to_dict()
    }
    return render_template('admin/index.html', data=data)


@admin_blu.route('/login', methods=["POST", "GET"])
def login():

    if request.method == "GET":
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", None)
        if user_id and is_admin:
            return redirect(url_for("admin.index"))
        return render_template('admin/login.html')

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数错误")

    try:
        user = User.query.filter(User.mobile==username, User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="用户信息查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="未查询到用户信息")

    if not user.check_passowrd(password):
        return render_template('admin/login.html', errmsg="用户名或者密码错误")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name
    session["is_admin"] = user.is_admin

    return redirect('/admin/index')


@admin_blu.route("/user_count")
def user_count():
    total_count = 0
    mon_count = 0
    day_count = 0
    # 所有用户
    try:
        total_count = User.query.filter(User.is_admin==False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 月新增用户
    time_now = time.localtime()
    begin_mon_date = datetime.strptime(("%d-%02d-01" % (time_now.tm_year, time_now.tm_mon)), "%Y-%m-%d")

    try:
        mon_count = User.query.filter(User.is_admin==False, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 日新增
    begin_day_date = datetime.strptime(("%d-%02d-%02d" % (time_now.tm_year, time_now.tm_mon, time_now.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 折线图数据
    active_time = []
    active_count = []
    begin_today_date = datetime.strptime('%d-%02d-%02d' % (time_now.tm_year, time_now.tm_mon, time_now.tm_mday), "%Y-%m-%d")
    for i in range(0, 31):
        begin_date = begin_today_date - timedelta(days=i)
        end_date = begin_today_date - timedelta(days=(i-1))
        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date, User.last_login < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template("admin/user_count.html", data=data)


@admin_blu.route('/user_list')
def user_list():
    try:
        page =int(request.args.get("page", 1))
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    user_list = []
    cur_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin==False).paginate(page, 10)
        user_list = paginate.items
        total_page = paginate.pages
        cur_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = []
    for user in user_list:
        user_dict_li.append(user.to_admin_dict())

    data = {
        "user_dict_li": user_dict_li,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template('admin/user_list.html', data=data)


@admin_blu.route('/news_review')
@user_login_data
def news_review():

    page = request.args.get("page", 1)
    keywords = request.args.get("keywords", None)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    cur_page = 1
    total_page = 1
    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, 10, False)
        news_list = paginate.items
        cur_page = paginate.page
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_review_dict())
    print(news_dict_li)
    data = {
        "total_page": total_page,
        "current_page": cur_page,
        "news_dict_li": news_dict_li
    }
    return render_template('admin/news_review.html', data=data)
