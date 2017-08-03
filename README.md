# 163music
网易云音乐歌曲热门评论爬虫

## 项目结构

### - cihper.py
获取歌手跟歌曲评论的api加密算法，包含AES和RSA。

### - api.py
- `get_artlists(offset)` 获取歌手
- `get_top50(artist_id)` 获取歌手热门50首歌曲，仅爬取歌手的热门50首歌曲，不是全部。
- `get_comments(song_id)` 获取歌曲评论，仅保存热门评论。

### dbs.py
数据库相关操作，这里利用`collections.namedtuple`来实现简单的orm。
- `Artist` `Song` `Comment` `User` `Log` 项目中5个数据Model，对应数据库中的五张表。
- `ConnectionPool` 数据库连接池，利用上下文和threading.local()是实现多线程的连接管理。
- `insert` `query`...数据库操作方法。

### crawl.py
具体的爬虫实现模块，爬虫启动入口。
- `CrawlTask`爬虫任务基本，管理线程池，处理爬虫结果，简单反爬处理。
- `ArtistCrawlTask` 歌手爬虫
- `SongCrawlTask` 歌曲爬虫
- `CommentCrawlTask` 评论爬虫

### settings.py
配置模块，数据库连接参数、数据库连接池大小、爬虫线程池大小、爬取限制等配置

### log.py
日志配置模块，输出到控制台等级为DEBUG，输出到文件等级为INFO。

### 163music.sql
数据库定义文件，相关的表定义都在里面。

## 使用

1. `clone https://github.com/xiaoqqqqqq/163music.git`
2. 创建数据库和表，连接进入mysql的shell。`mysql> source 163music/163music.sql`。
3. 修改settings.py，配置好相关的数据库连接参数。
4. 启动爬虫`python crawl.py`。

更多介绍看[这里](https://xiaoqqqqqq.github.io/2017/08/02/crawl-163music/)