#!/usr/bin/env python

__all__ = ['acfun_download']

import re
from common import *
from iask import iask_download_by_id
from youku import youku_download_by_id
from tudou import tudou_download_by_iid
import json

def get_srt_json(id):
	url = 'http://comment.acfun.tv/%s.json' % id
	return get_html(url)

def acfun_download_by_id(id, title):
	info = json.loads(get_html('http://www.acfun.tv/api/getVideoByID.aspx?vid=' + id))
	t = info['vtype']
	if t == 'sina':
		iask_download_by_id(id, title)
	elif t == 'youku':
		youku_download_by_id(id, title)
	elif t == 'tudou':
		tudou_download_by_iid(id, title)
	else:
		raise NotImplementedError(t)

	srt = get_srt_json(info['vid'])
	with open(title + '.json', 'w') as x:
		x.write(srt)

def acfun_download(url):
	assert re.match(r'http://www.acfun.tv/v/ac(\d+)', url)
	html = get_html(url).decode('utf-8')

	title = r1(r'<span id="title-article" class="title"[^<>]*>([^<>]+)</span>', html)
	assert title
	title = unescape_html(title)
	title = escape_file_path(title)
	title = title.replace(' - AcFun.tv', '')

	id = r1(r"flashvars = {'id':'(\d+)'", html)
	acfun_download_by_id(id, title)


download = acfun_download
download_playlist = playlist_not_supported('acfun')

def main():
	script_main('acfun', acfun_download)

if __name__ == '__main__':
	main()

