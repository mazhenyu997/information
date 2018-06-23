from info.modules.profile import profile_blu
from flask import render_template, g, redirect, request, jsonify

from info.utils.common import user_login_data
from info.utils.response_code import RET


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


@profile_blu.route('/pic_info', methods=["POST", "GET"])
@user_login_data
def pic_info():
    if request.method == "GET":
        user = g.user
        data = {
            "user": user.to_dict() if user else None,
        }
        return render_template("news/user_pic_info.html", data=data)

    nick_name = request.json.get("nick_name", '')
    signature = request.json.get("signature", '')
    gender = request.json.get("gender", '')

    if not all([nick_name, gender, signature]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in (["WOMAN", "MAN"]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.gender = gender
    user.signature = signature
    user.nick_name = nick_name

    return jsonify(errno=RET.OK, errmsg="OK")
