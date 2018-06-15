import random
import re
from datetime import datetime

from flask import request, abort, current_app, make_response, json, jsonify, session
from info import db
from info import redis_store, constants
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu
from info.utils.captcha.captcha import captcha


# 退出登陆
@passport_blu.route('/logout')
def logout():
    """

    :return:
    """
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nick_name", None)

    return jsonify(errno=RET.OK, errmsg="退出登陆")


# 登陆
@passport_blu.route('/login', methods=["POST"])
def login():
    """

    :return:
    """
    params_dict = request.json
    mobile = params_dict.get("mobile")
    passwd = params_dict.get("password")

    if not all([mobile, passwd]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 校验手机号
    if not re.match('1[35789]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 先查询手机号是否存在
    cur_user = User.query.filter(User.mobile == mobile).first()
    if not cur_user:
        return jsonify(errno=RET.DBERR, errmsg="用户不存在")

    # 校验密码
    if not cur_user.check_passowrd(passwd):
        return jsonify(errno=RET.PWDERR, errmsg="用户密码错误")

    # 保存登陆状态
    session["user_id"] = cur_user.id
    session["mobile"] = cur_user.mobile
    session["nick_name"] = cur_user.nick_name

    return jsonify(errno=RET.OK, errmsg="登陆成功")


# 注册
@passport_blu.route('/register', methods=["POST"])
def register():
    """
    1 获取参数
    2 校验参数
    3 取到服务器保存的真实验证码内容对比
    4 初始化user
    5 将user添加到模型
    6 返回响应

    :return:
    """
    params_dict = request.json
    mobile = params_dict.get("mobile", '')
    smscode = params_dict.get("smscode", '')
    password = params_dict.get("password", '')

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验手机号
    if not re.match('1[35789]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 取真实验证码
    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="验证码已过期")

    if real_sms_code != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.last_login = datetime.now()
    user.password = password
    # 保存数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    发送短信的逻辑
    1 获取参数：手机号，图片验证码内容，图片验证码编号（随机值）
    2 校验参数，
    3 先从redis中获取真实的验证码内容
    4 与用户的验证码内容进行对比，如果不通过返回验证码输入错误
    5 如果一致，生成验证码的内容，随机数
    6 发送短信验证码
    7 告知发送结果
    :return:
    """
    # return jsonify(errno=RET.OK, errmsg="发送成功")
    # params_dict = json.loads(request.data)
    params_dict = request.json
    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")
    if not all([mobile, image_code, image_code_id]):
        # 返回一个json格式的数据
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 校验手机号
    if not re.match('1[35789]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    try:
        real_code = redis_store.get("ImageCodeId"+image_code_id)
        # real_code_type = type(real_code)
        # print("real_code_type"+real_code_type)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not real_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")

    if real_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    sms_code_str = "%06d" % random.randint(0, 999999)
    # sms_code_str = 99999
    print(sms_code_str)
    current_app.logger.debug("短信验证码内容是%s" % sms_code_str)

    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5])

    result = 0

    if result != 0:
        # 短信发送失败
        return jsonify(errno=RET.THIRDERR, errmsg="短信发送失败")

    # 保存验证码到redis
    try:
        redis_store.set("SMS_" + mobile, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)

    # 告知发送结果
    return jsonify(errno=RET.OK, errmsg="发送成功")


@passport_blu.route('/image_code')
def get_image_code():
    """"生成图片验证码
    1 取参数
    2 判断参数是否有值
    3 生成图片验证码
    4 保存图片验证码内容到redis
    5 返回验证码图片

    """
    # args取到URL中？后面的参数
    image_code_id = request.args.get("imageCodeId", "")

    if not image_code_id:
        return abort(403)

    # 生成图片验证码
    name, text, image = captcha.generate_captcha()

    # 保存图片验证码内容到redis
    try:
        redis_store.set("ImageCodeId"+ image_code_id, text, 300)

    except Exception as e:

        current_app.logger.error(e)
        abort(500)

    # 返回验证码图片

    # 返回的content—type应该是图片而不是html/ ，谷歌可以正确识别，其他的浏览器不一定识别所以需要指定
    response = make_response(image)
    response.headers["Content_Type"] = "image/jpg"
    return response

