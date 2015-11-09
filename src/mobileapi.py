#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

from json import loads
from urllib2 import Request, urlopen
from urllib import urlencode


class TV3PlayMobileApi(object):
	def __init__(self, region):
		self.region = region

	def getAllFormats(self):
		formats = list()
		f = self.format()
		if f:
			if ' Error ' in f:
				return f
			for section in f['sections']:
				formats.extend(section['formats'])
		return formats

	def getVideos(self, category):
		return self._call_api('formatcategory/%s/video' % category)

	def format(self):
		return self._call_api('format')

	def detailed(self, formatId):
		return self._call_api('detailed', {'formatid': formatId})

	def _call_api(self, url, params = None):
		if url[0:4] != 'http':
			url = ' http://%s/mobileapi/%s' % (self.region, url)

		if params:
			url += '?' + urlencode(params)

		content = self._http_request(url)

		if content:
			if ' Error ' in content:
				return content
			try:
				return loads(content)
			except Exception, ex:
				return {" Error " : "in call_api: %s" % ex}
		else:
			return []

	def _http_request(self, url):
		try:
			r = Request(url, headers={
					'user-agent': 'TV3 Play/1.0.3 CFNetwork/548.0.4 Darwin/11.0.0'
				})
			u = urlopen(r)
			content = u.read()
			u.close()
			return content
		except Exception as ex:
			return {" Error " : "in http_request: %s" % ex}

