import logging

from redis import StrictRedis


class Config(object):
    DEBUG = True
    SECRET_KEY = "adfafvvaf2sad3danaasddfasfafa"

    # mysql添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysqlmmm@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 在请求结束时会自动执行一次 db.commit()
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # redis 配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session 保存配置
    SESSION_TYPE = "redis"
    # 开启签名
    SESSION_USE_SIGNER = True
    # 设置session保存位置
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    # 禁止永久过期
    SESSION_PERMANENT = False
    # 手动设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


# 开发环境配置
class DevelopConfig(Config):
    DEBUG = True


# 生产环境配置
class ProductConfig(Config):
    DEBUG = False


# 测试环境配置
class TestConfig(Config):
    DEBUG = True
    TESTING = True
    LOG_LEVEL = logging.ERROR


config = {
    "develop": DevelopConfig,
    "product": ProductConfig,
    "test": TestConfig
}


