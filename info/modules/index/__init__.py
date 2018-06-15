from flask import Blueprint


# 1 导入蓝图  2 创建蓝图对象  3 蓝图的路由

index_blu = Blueprint("index", __name__)

from . import views