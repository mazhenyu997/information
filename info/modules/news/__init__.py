# 新闻详情的蓝图
from flask import Blueprint


# 1 导入蓝图  2 创建蓝图对象  3 蓝图的路由

news_blu = Blueprint("news", __name__, url_prefix="/news")

from . import views