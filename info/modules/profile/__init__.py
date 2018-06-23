# 用户当前模块中

from flask import Blueprint


# 1 导入蓝图  2 创建蓝图对象  3 蓝图的路由

profile_blu = Blueprint("profile", __name__, url_prefix="/user")

from . import views
