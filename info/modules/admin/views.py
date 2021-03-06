from datetime import datetime, timedelta
import time

from info import db
from info.modules.admin import admin_blu
from flask import render_template, request, jsonify, current_app, session, redirect, url_for, g, abort
from info.models import User, News, Category
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


# 用户统计
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


# 用户列表
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


# 待审核列表
@admin_blu.route('/news_review')
def news_review():

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        filters = [News.status != 0]
        # 如果有关键词
        if keywords:
            # 添加关键词的检索选项
            filters.append(News.title.contains(keywords))

        # 查询
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, 10, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())
    data = {
               "total_page": total_page,
               "current_page": current_page,
               "news_li": news_dict_list
            }
    return render_template('admin/news_review.html', data=data)


@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return render_template('admin/news_review_detail.html', data={"data": "未查询到此新闻"})

    data = {
        "news": news.to_dict()
    }
    return render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_review_action', methods=["POST"])
def news_review_action():
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        news.status = 0

    elif action == "reject":
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        news.reason = reason
        news.status = -1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


# 新闻版式编辑
@admin_blu.route('/news_edit')
def news_edit():

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        filters = [News.status == 0]
        # 如果有关键词
        if keywords:
            # 添加关键词的检索选项
            filters.append(News.title.contains(keywords))

        # 查询
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, 10, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())
    data = {
               "total_page": total_page,
               "current_page": current_page,
               "news_li": news_dict_list
            }
    return render_template('admin/news_edit.html', data=data)


@admin_blu.route('/news_edit_detail', methods=["POST", "GET"])
def news_edit_detail():
    if request.method == "GET":

        news_id = request.args.get("news_id")
        if not news_id:
            abort(404)
        try:
            news_id = int(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', err_msg="参数错误")

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', err_msg="查询错误")

        if not news:
            return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

        # 查询分类数据
        categories = []

        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', err_msg="查询错误")

        category_dict_li = []
        for category in categories:
            cate_dict = category.to_dict()
            if category.id == news.category_id:
                cate_dict["is_selected"] = True
            category_dict_li.append(cate_dict)

        category_dict_li.pop(0)

        data = {
            "news": news.to_dict(),
            "categories": category_dict_li

        }
        return render_template('admin/news_edit_detail.html', data=data)

    elif request.method == "POST":
        news_id = request.form.get("news_id")
        title = request.form.get("title")
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")

        if not all([title, digest, content, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

        if not news:
            return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
        '''
        if index_image:
            try:
                index_image = index_image.read()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

            # 2. 将标题图片上传到七牛
            try:
                key = storage(index_image)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
            news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        '''

        news.title = title
        news.digest = digest
        news.content =content
        news.category_id = category_id

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

        return jsonify(errno=RET.OK, errmsg="OK")


# 新闻分类
@admin_blu.route('/news_type', methods=['POST', 'GET'])
def news_type():
    if request.method == "GET":

        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html', err_msg="查询错误")

        category_dict_li = []
        for category in categories:
            cate_dict = category.to_dict()
            category_dict_li.append(cate_dict)

        category_dict_li.pop(0)

        data = {
            "categories": category_dict_li

        }
        return render_template('admin/news_type.html', data=data)

    category_name = request.json.get("name")
    category_id = request.json.get("id")

    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    if category_id:
        try:
            category_id = int(category_id)
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
        if not category:
            return jsonify(errno=RET.DBERR, errmsg="未查询到分类数据")

        category.name = category_name

    else:
        category = Category()
        category.name = category_name
        db.session.add(category)

    return jsonify(errno=RET.OK, errmsg="OK")

