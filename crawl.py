from datetime import datetime
from array import array
import time
import threading
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import api
import dbs
from log import logger

import settings


class CrawlTask(object):
    '''爬虫基类'''

    pool = ThreadPoolExecutor(settings.CRAWL_POOL_SIZE, 'craw_thread')
    local = threading.local()  # 记录每个线程发起的请求数

    def __init__(self, arg):
        self.arg = arg

    def save_result(self, result, msg):
        '''保存爬取的结果'''
        log = dbs.Log(None, self.__class__.__name__, self.arg, result, msg, datetime.now())
        dbs.insert(log, 'result', 'crawl_date')

    def __call__(self):
        '''爬取 解析 保存爬取的信息和结果'''
        try:
            logger.info('{} start crawl...'.format(self))
            rowcount = self.crawl_and_save()  # 爬取并保存到数据中去
            self.save_result(1, str(rowcount))  # 记录已经爬过了,保存到数据库中去
            logger.info('{} end crawl, insert record:{}...'.format(self, rowcount))
            self.check_request_times()
        except Exception as e:
            logger.exception('{} exception:{}'.format(self, e))
            self.save_result(0, str(e))  # 记录爬取异常的

    def crawl_and_save(self):
        '''调用具体api获取页面和解析保存到数据库中的逻辑，由具体子类实现'''
        pass

    @classmethod
    def check_request_times(cls):
        '''检查当前线程已经发起了多少请求，到一定数量了就sleep一下'''
        if not hasattr(cls.local, 'times'):
            cls.local.times = 0
        else:
            cls.local.times += 1

        # 每个线程发起CRAWL_THREAD_SIZE个请求后就 暂停CRAWL_THREAD_SLEEP_TIME分钟 可自行调整
        if cls.local.times > settings.CRAWL_THREAD_SIZE:
            logger.info('{} sleep...'.format(threading.current_thread().name))
            time.sleep(settings.CRAWL_THREAD_SLEEP_TIME)
            cls.local.times = 0
            logger.info('{} restart...'.format(threading.current_thread().name))

    @classmethod
    def start_task(cls, arg):
        task = cls(arg)
        cls.pool.submit(task)

    @classmethod
    def start(cls):
        '''过滤过未爬取的任务 开启爬取'''
        pass

    @classmethod
    def wait_tasks_done(cls):
        '''等待任务爬取完毕'''
        while cls.pool._work_queue.qsize() != 0:
            time.sleep(5)

    def __str__(self):
        '''CrawlTask(1)'''
        return '{}({})'.format(self.__class__.__name__, self.arg)


class ArtistCrawlTask(CrawlTask):
    '''爬取歌手'''

    def crawl_and_save(self):
        js = api.get_artlists(self.arg)
        artists = (dbs.Artist(j['id'], j['name'], self.arg) for j in js['artists'])
        rowcount = dbs.insert_list(artists)
        return rowcount

    @classmethod
    def start(cls):
        '''过滤过未爬取的任务 开启爬取'''

        # 歌手所在页数
        pages = range(640)  # 歌手页数测试在640左右，精确数值可自行调用api.get_artlists来测试

        # 拿到已经爬取过了的任务
        done_pags = dbs.raw_query('select arg from log where task_name=%s and result=%s', (cls.__name__, 1))
        done_pags = array('L', (i[0] for i in done_pags))

        # 开启未爬取的任务
        for page in pages:
            if page not in done_pags:
                cls.start_task(page)

        cls.wait_tasks_done()


class SongCrawlTask(CrawlTask):
    '''爬取歌手的热门50首歌曲'''

    def crawl_and_save(self):
        # 获取热门50首 解析 保存到数据库
        html = api.get_top50(self.arg)
        root = BeautifulSoup(html, 'lxml')
        songs = (dbs.Song(a['href'].replace('/song?id=', ''), a.text.strip(), 0, self.arg) for a in root.select('.f-hide a'))
        rowcount = dbs.insert_list(songs)
        return rowcount

    @classmethod
    def start(cls):
        '''过滤过未爬取的任务 开启爬取'''

        artists = (i[0] for i in dbs.raw_query('select id from artist'))

        # 拿到已经爬取过了的任务
        done_artists = dbs.raw_query('select arg from log where task_name=%s and result=%s', (cls.__name__, 1))
        done_artists = array('L', (i[0] for i in done_artists))
        # 开启未爬取的任务
        for artist in artists:
            if artist not in done_artists:
                cls.start_task(artist)

        cls.wait_tasks_done()


class CommentCrawlTask(CrawlTask):
    '''爬取评论'''

    def crawl_and_save(self):
        js = api.get_comments(self.arg)

        # 更新所在歌曲的总评论数
        song = dbs.query_one(dbs.Song, id=self.arg)
        dbs.insert(song._replace(comment_count=js['total']), 'comment_count')

        # 保存评论的用户
        users = (dbs.User(j['user']['userId'], j['user']['nickname']) for j in js['hotComments'])
        dbs.insert_list(users)

        # 保存评论
        comments = (dbs.Comment(j['commentId'], j['content'], j['likedCount'], j['user']['userId'], self.arg) for j in js['hotComments'])
        rowcount = dbs.insert_list(comments)
        return rowcount

    @classmethod
    def start(cls):
        '''过滤过未爬取的任务 开启爬取'''

        songs = (i[0] for i in dbs.raw_query('select id from song'))

        # 拿到已经爬取过了的任务
        done_songs = dbs.raw_query('select arg from log where task_name=%s and result=%s', (cls.__name__, 1))
        done_songs = array('L', (i[0] for i in done_songs))

        # 开启未爬取的任务
        for song in songs:
            if song not in done_songs:
                cls.start_task(song)

        cls.wait_tasks_done()


if __name__ == '__main__':
    ArtistCrawlTask.start()
    time.sleep(5)
    SongCrawlTask.start()
    time.sleep(5)
    CommentCrawlTask.start()
