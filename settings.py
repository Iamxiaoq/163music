# 连接数据库参数
DB = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456',
    'db': '163music',
    'charset': 'utf8',
}

# 数据库连接池大小
CONNECTION_POOL_SIZE = 10

# 爬虫线程池大小
CRAWL_POOL_SIZE = 15

# 爬虫线程发起多少个请求后暂停
CRAWL_THREAD_SIZE = 30

# 爬虫线程暂停多少秒
CRAWL_THREAD_SLEEP_TIME = 10 * 60
