import requests
from cihper import encry_post_data


art_url = 'http://music.163.com/weapi/artist/list?csrf_token='
headers = {
    'Origin': 'http://music.163.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Referer': 'http://music.163.com/discover/artist/signed/',
}


def get_artlists(offset):
    url = 'http://music.163.com/weapi/artist/list?csrf_token='
    data = {"categoryCode": "5001", "offset": 60 * offset, "total": "false", "limit": "60", "csrf_token": ""}
    return post(url, data)


# proxy = {'http': 'http://localhost:9999'}
proxy = None


def get_top50(artist_id):
    url = 'http://music.163.com/artist?id=' + str(artist_id)
    res = requests.get(url, headers=headers, proxies=proxy)
    return res.text


def get_comments(song_id):
    url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_{}?csrf_token='.format(song_id)
    data = {"rid": "R_SO_4_" + str(song_id), "offset": "0", "total": "true", "limit": "20", "csrf_token": ""}
    return post(url, data)


def post(url, data):
    data = encry_post_data(data)
    res = requests.post(url, data, headers=headers, proxies=proxy)
    return res.json()
