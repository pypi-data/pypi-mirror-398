from ..xfreehd_api import Client

client = Client()
url = "https://beta.xfreehd.com/album/14805/woman-boy-18-nudists"
album = client.get_album(url)

def test_images():
    images = album.get_all_images()
    assert isinstance(images, list)
    assert len(images) > 0

def test_images_by_page():
    images = album.get_images_by_page(page=2)
    assert isinstance(images, list)
    assert len(images) > 0