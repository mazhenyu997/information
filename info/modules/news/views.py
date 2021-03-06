from info import db
from info.models import News, Comment, CommentLike, User
from info.modules.news import news_blu
from flask import render_template, current_app, abort, g, request, jsonify

from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    user = g.user
    # 右侧新闻的逻辑
    news_right_list = []
    try:
        news_right_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    # 将列表中的对象转为列表中的字典
    news_dict_list = []
    for news in news_right_list:
        news_dict_list.append(news.to_basic_dict())

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    if not news:
        # 返回数据未找到的页面
        abort(404)

    news.clicks += 1

    is_collected = False
    # 判断用户是否收藏过该新闻
    if g.user:
        if news in g.user.collection_news:
            is_collected = True

    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id==news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    if g.user:
        # 查询当前用户在当前新闻有那些被点赞过
        comment_ids = [comment.id for comment in comments]
        comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids), CommentLike.user_id==g.user.id).all()
        comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]

    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        if g.user:
            if comment.id in comment_like_ids:
                comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    is_followed = False

    if news.user and user:
        if news.user in user.followed:
             is_followed = True
    data = {
        "news": news.to_dict(),
        "is_collected": is_collected,
        "user": g.user.to_dict() if g.user else None,
        "news_dict_li": news_dict_list,
        "comments": comment_dict_li,
        "is_followed": is_followed
    }
    return render_template('news/detail.html', data=data)


@news_blu.route("/news_collect", methods=['POST'])
@user_login_data
def news_collect():
    """新闻收藏"""

    user = g.user
    json_data = request.json
    news_id = json_data.get("news_id")
    action = json_data.get("action")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if not news_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


# 新闻评论
@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def comment_news():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="ok", data=comment.to_dict())


@news_blu.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """
    新闻点赞
    :return:
    """
    user = g.user
    json_data = request.json
    comment_id = json_data.get("comment_id")
    # news_id = json_data.get("news_id")
    action = json_data.get("action")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if not all([ comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment_id = int(comment_id)
        # news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        comment_like_model = CommentLike.query.filter(CommentLike.user_id==user.id, CommentLike.comment_id==comment.id).first()
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment.id
            db.session.add(comment_like_model)

    else:
        # 取消点赞
        comment_like_model = CommentLike.query.filter(CommentLike.user_id==user.id, CommentLike.comment_id==comment.id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comment.like_count -= 1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据操作失败")

    return jsonify(errno=RET.OK, errmsg="ok")


# 关注和取消关注
@news_blu.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():

    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请先登陆")

    user_id = request.json.get("user_id")
    action = request.json.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        other = User.query.get(user_id)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="查询失败")

    if action == "follow":
        if other not in user.followed:

            user.followed.append(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="已关注")

    else:
        if other in user.followed:
            user.followed.remove(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="未关注")

    return jsonify(errno=RET.OK, errmsg="操作成功")









