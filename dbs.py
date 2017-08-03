from warnings import filterwarnings
import threading
from queue import Queue
from collections import namedtuple
import pymysql

import settings


filterwarnings('ignore', category=pymysql.err.Warning)  # 压制mysql警告


Artist = namedtuple('Artist', 'id name page')  # 歌手表
Song = namedtuple('Song', 'id name comment_count artist_id')  # 歌曲表
Comment = namedtuple('Comment', 'id content liked_count user_id song_id')  # 评论表
User = namedtuple('User', 'id nickname')  # 用户表
Log = namedtuple('Log', 'id task_name arg result msg crawl_date')  # 日志表 用于去重


class ConnectionPool(object):
    '''数据库连接池 使用上下文管理多线程连接'''

    def __init__(self):
        self._qsize = settings.CONNECTION_POOL_SIZE  # 最大长度
        self._current_size = 0  # 当前已经分配
        self._queue = Queue(self._qsize)
        self._lock = threading.Lock()
        self._local = threading.local()

    def __enter__(self):
        self.adjust_size()
        if hasattr(self._local, 'conn'):  # 同一线程下不可嵌套使用
            raise Exception('thread: {} already has connection.'.format(threading.current_thread()))
        conn = self._queue.get()
        self._local.conn = conn
        return conn

    def __exit__(self, exc_type, exc_value, traceback):
        self._queue.put(self._local.conn)
        del self._local.conn

    def adjust_size(self):
        '''调整连接池大小，未达到最大长度时添加新连接'''
        if self._current_size >= self._qsize:
            return
        with self._lock:
            if self._current_size >= self._qsize:
                return
            conn = pymysql.connect(**settings.DB)
            self._queue.put(conn)
            self._current_size += 1


_pool = ConnectionPool()


def _insert(item, conn, *duplicate_fields):
    table_name = item.__class__.__name__.lower()
    fields = ','.join(item._fields)
    values = ('%s,' * len(item._fields))[:-1]
    if not duplicate_fields:
        sql = 'insert ignore {table_name}({fields}) values({values})'.format(**locals())
    else:
        duplicate_update_fields = (''.join('{0}=values({0}),'.format(field) for field in duplicate_fields))[:-1]
        sql = 'insert {table_name}({fields}) values({values}) on duplicate key update {duplicate_update_fields}'.format(**locals())
    with conn.cursor() as cursor:
        return cursor.execute(sql, item)


def insert(item, *duplicate_fields):
    '''插入nametupled实例
    duplicate_fields:记录重复时更新哪些字段
    '''
    with _pool as conn:
        rowcount = _insert(item, conn, *duplicate_fields)
        conn.commit()
        return rowcount


def insert_list(items, *duplicate_fields):
    '''一次插入多个namedtuple实例
    duplicate_fields:记录重复时更新哪些字段
    '''
    with _pool as conn:
        rowcount = sum(_insert(item, conn, *duplicate_fields) for item in items)
        conn.commit()
        return rowcount


def query(item_class, size=None, **kwargs):
    '''根据namedtuple类名来查询记录
    size:
        None:查询所有
        1: 查询单条记录
        5: 查询5条记录
        (limit, offset):分页
    kwargs:查询条件，如id=1, name='xiaoq'
    '''
    table_name = item_class.__name__.lower()
    fields = ','.join(item_class._fields)
    sql = 'select {fields} from {table_name}'.format(**locals())
    if kwargs:
        where = (''.join('{}=%s and '.format(k) for k in kwargs))[:-5]
        sql = sql + ' where ' + where
    if isinstance(size, tuple):
        sql = sql + ' limit {} offset {}'.format(*size)
    with _pool as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(kwargs.values()))
            if size == 1:  # query one
                rs = cursor.fetchone()
                if rs:
                    return item_class(*rs)
            else:  # query size
                rs = cursor.fetchmany(size) if isinstance(size, int) else cursor.fetchall()
                if rs:
                    return (item_class(*r) for r in rs)


def query_one(item_class, **kwargs):
    '''查询单条记录'''
    return query(item_class, size=1, **kwargs)


def raw_query(sql, args=None):
    '''执行原始的sql查询'''
    with _pool as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()
