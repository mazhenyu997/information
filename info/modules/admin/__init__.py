from flask import Blueprint


# 1 导入蓝图  2 创建蓝图对象  3 蓝图的路由

admin_blu = Blueprint("admin", __name__, url_prefix='/admin')

from . import views