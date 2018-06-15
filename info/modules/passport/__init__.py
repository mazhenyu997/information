# 登陆注册的业务逻辑都放在当前模块中

from flask import Blueprint


# 1 导入蓝图  2 创建蓝图对象  3 蓝图的路由

passport_blu = Blueprint("passport", __name__, url_prefix="/passport")

from . import views