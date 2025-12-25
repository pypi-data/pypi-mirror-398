import re


REGEX_THUMBNAIL = re.compile(r'data-img="(.*?)"')
REGEX_ALBUM_START = re.compile(r'Showing (.*?) t')
REGEX_ALBUM_END = re.compile(r'o (.*?) o')
REGEX_ALBUM_TOTAL = re.compile(r'f (.*?) photos')