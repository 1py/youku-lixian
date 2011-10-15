#!/usr/bin/env python

import urllib2
import json
from random import randint
from time import time
import re
import os.path
import shutil

def youku_url(url):
	if re.match(r'http://v.youku.com/v_show/id_(\w+).html', url):
		return url
	m = re.match(r'http://player.youku.com/player.php/sid/(\w+)/v.swf', url)
	if m:
		return 'http://v.youku.com/v_show/id_%s.html' % m.group(1)
	if re.match(r'^\d+$', url):
		return 'http://v.youku.com/v_show/id_%s.html' % url
	raise Exception('Invalid youku URL: '+url)

def parse_page(url):
	url = youku_url(url)
	page = urllib2.urlopen(url).read()
	id2 = re.search(r"var\s+videoId2\s*=\s*'(\S+)'", page).group(1)
	title = re.search(r'<meta name="title" content="([^"]*)">', page).group(1).decode('utf-8')
	title = title.replace(u' - \u89c6\u9891 - \u4f18\u9177\u89c6\u9891 - \u5728\u7ebf\u89c2\u770b', '')
	subtitle = re.search(r'<span class="subtitle" id="subtitle">([^<>]*)</span>', page)
	if subtitle:
		subtitle = subtitle.group(1).decode('utf-8')
	if subtitle == title:
		subtitle = None
	return id2, title, subtitle

def get_info(videoId2):
	return json.loads(urllib2.urlopen('http://v.youku.com/player/getPlayList/VideoIDS/'+videoId2).read())

def find_video(info, stream_type=None):
	#key = '%s%x' % (info['data'][0]['key2'], int(info['data'][0]['key1'], 16) ^ 0xA55AA5A5)
	segs = info['data'][0]['segs']
	types = segs.keys()
	if not stream_type:
		for x in ['hd2', 'mp4', 'flv']:
			if x in types:
				stream_type = x
				break
		else:
			raise NotImplementedError()

	seed = info['data'][0]['seed']
	source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\\:._-1234567890")
	mixed = ''
	while source:
		seed = (seed * 211 + 30031) & 0xFFFF
		index = seed * len(source) >> 16
		c = source.pop(index)
		mixed += c

	ids = info['data'][0]['streamfileids'][stream_type].split('*')[:-1]
	vid = ''.join(mixed[int(i)] for i in ids)

	sid = '%s%s%s' % (int(time()*1000), randint(1000, 1999), randint(1000, 9999))

	urls = []
	for s in segs[stream_type]:
		no = '%02d' % int(s['no'])
		url = 'http://f.youku.com/player/getFlvPath/sid/%s_%s/st/%s/fileid/%s%s%s?K=%s&ts=%s' % (sid, no, 'flv', vid[:8], no, vid[10:], s['k'], s['seconds'])
		urls.append(url)
	return urls

def youku_download(url, output_dir='', stream_type=None):
	id2, title, subtitle = parse_page(url)
	if subtitle:
		title += '-' + subtitle
	info = get_info(id2)
	urls = find_video(info, stream_type)
	flvs = []
	for i, url in enumerate(urls):
		filename = '%s[%02d].flv' % (title, i)
		filepath = os.path.join(output_dir, filename)
		flvs.append(filepath)
		print 'Downloading', filename, '...'
		response = urllib2.urlopen(url)
		with open(filepath, 'wb') as output:
			shutil.copyfileobj(response, output)
	from flv_join import concat_flvs
	concat_flvs(flvs, os.path.join(output_dir, title+'.flv'))
	for flv in flvs:
		os.remove(flv)

if __name__ == '__main__':
	import sys
	for url in sys.argv[1:]:
		youku_download(url)

