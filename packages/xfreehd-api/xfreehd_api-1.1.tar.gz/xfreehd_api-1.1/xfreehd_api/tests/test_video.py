from ..xfreehd_api import Client


client = Client()
url = "https://beta.xfreehd.com/video/929816/tap-out-pmv"
video = client.get_video(url)

def test_title():
    assert isinstance(video.title, str) and len(video.title) > 0

def test_likes():
    assert isinstance(video.likes, str) and len(video.likes) > 0

def test_dislikes():
    assert isinstance(video.dislikes, str) and len(video.dislikes) > 0

def test_publish_date():
    assert isinstance(video.publish_date, str) and len(video.publish_date) > 0

def test_views():
    assert isinstance(video.views, str) and len(video.views) > 0

def test_categories():
    assert isinstance(video.categories, list) and len(video.categories) > 0

def test_tags():
    assert isinstance(video.tags, list) and len(video.tags) > 0

def test_author():
    assert isinstance(video.author, str) and len(video.author) > 0

def test_thumbnail():
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 0

def test_cdn_urls():
    assert isinstance(video.cdn_urls, list) and len(video.cdn_urls) > 0

def test_download_sd():
    assert video.download(quality="sd") is True

def test_download_hd():
    assert video.download(quality="hd") is True
