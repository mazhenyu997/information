import os
import random
import time

from info import db
from info.constants import QINIU_DOMIN_PREFIX
from info.models import Category, News
from info.modules.profile import profile_blu
from flask import render_template, g, redirect, request, jsonify, current_app

from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


# 用户中心首页
@profile_blu.route('/info')
@user_login_data
def user_info():
    user = g.user

    if not user:
        return redirect("/ ")
    data = {
        "user": user.to_dict() if user else None,
    }
    return render_template("news/user.html", data=data)


# 基本信息展示
@profile_blu.route('/base_info', methods=["POST", "GET"])
@user_login_data
def base_info():

    if request.method == "GET":
        user = g.user
        data = {
            "user": user.to_dict() if user else None,
        }
        return render_template("news/user_base_info.html", data=data)

    nick_name = request.json.get("nick_name", '')
    signature = request.json.get("signature", '')
    gender = request.json.get("gender", '')

    if not all([nick_name, gender, signature]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in(["WOMAN", "MAN"]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.gender = gender
    user.signature = signature
    user.nick_name = nick_name

    return jsonify(errno=RET.OK, errmsg="OK")


# 上传头像
@profile_blu.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        return render_template('news/user_pic_info.html', data={"user": user.to_dict()})

    # 1. 获取到上传的文件
    try:
        avatar_file = request.files.get("avatar")

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="读取文件出错")

    # 2. 再将文件上传到七牛云，七牛账号失效，保存在本地
    '''
    try:
        url = storage(avatar_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
    
    try:
        avatar_name = str(int(time.time())) + avatar_file.name
        print(avatar_file.name)
        destination = open(os.path.join("/Users/mazhenyu/Pictures/", avatar_name), 'wb+')
        destination.write(avatar_file.read())
        destination.close()
    except Exception as e:
        current_app.logger.error(e)
    '''
    # 3. 将头像信息更新到当前用户的模型中
    avatar_url = "http://chuantu.biz/t6/333/1529807592x-1404817844.jpg"
    # 设置用户模型相关数据
    user.avatar_url = avatar_url
    # 将数据保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户数据错误")

    # 4. 返回上传的结果<avatar_url>
    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": avatar_url})


# 修改密码
@profile_blu.route('/pass_info', methods=["POST", "GET"])
@user_login_data
def pass_info():

    if request.method == "GET":
        data = {}
        return render_template("news/user_pass_info.html", data=data)

    old_password = request.json.get("old_password", '')
    new_password = request.json.get("new_password", '')

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="修改成功")


# 用户收藏
@profile_blu.route('/collection', methods=["POST", "GET"])
@user_login_data
def collection():

    page = request.args.get('page', 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        page = 1

    # 查询
    user = g.user
    total_page = 1
    cur_page = 1
    try:
        paginate = user.collection_news.paginate(page, 10, False)
        cur_page = paginate.page
        total_page = paginate.pages
        news_li = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []

    for news in news_li:
        news_dict_li.append(news.to_dict())

    data = {
        "current_page": cur_page,
        "total_page": total_page,
        "collections": news_dict_li
    }
    return render_template("news/user_collection.html", data=data)


# 新闻发布
@profile_blu.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    if request.method == "GET":
        categories = None
        try:
            # 获取所有的分类数据
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        # 定义列表保存分类数据
        categories_dicts = []

        for category in categories if categories else []:
            # 获取字典
            cate_dict = category.to_dict()
            # 拼接内容
            categories_dicts.append(cate_dict)

        # 移除`最新`分类
        categories_dicts.pop(0)
        # 返回内容
        return render_template('news/user_news_release.html', data={"categories": categories_dicts})

    # POST 提交，执行发布新闻操作

    # 1. 获取要提交的数据
    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    '''
    # 1.2 尝试读取图片
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
    '''
    # 3. 初始化新闻模型，并设置相关数据
    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = "https://postimg.cc/image/ioj6dke2z/"
    news.category_id = category_id
    news.user_id = g.user.id
    news.status = 1

    # 4. 保存到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 5. 返回结果
    return jsonify(errno=RET.OK, errmsg="发布成功，等待审核")


# 新闻列表
@profile_blu.route('/news_list')
@user_login_data
def news_list():
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    user = g.user
    total_page = 1
    current_page = 1
    news_li = []
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, 6, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data = {"news_list": news_dict_li, "total_page": total_page, "current_page": current_page}
    return render_template('news/user_news_list.html', data=data)

