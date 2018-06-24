import os
import random
import time

from info import db
from info.constants import QINIU_DOMIN_PREFIX
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
