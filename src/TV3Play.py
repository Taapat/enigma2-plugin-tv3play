import os
from twisted.web.client import downloadPage

from enigma import ePicLoad, eServiceReference
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer

from . import _
import mobileapi


TMPDIR = "/tmp/tv3play/"
REGIONS = ["tv3play.lv",
	"tv3play.lt",
	"tv3play.ee",
	"tv3play.se",
	"tv3play.dk",
	"tv3play.no",
	"tv6play.se",
	"tv8play.se",
	"tv10play.se",
	"viasat4play.no",
	"play.novatv.bg"]


class TV3PlayAddon(object):
	def __init__(self, region):
		self.region = region
		self.api = mobileapi.TV3PlayMobileApi(region)

	def listPrograms(self):
		content = [(_("Return back..."), None, "back")]
		formats = self.api.getAllFormats()
		for series in formats:
			title = series["title"].encode("utf-8")
			image = str(mobileapi.IMAGE_URL % series["image"].replace(" ", "%20"))
			contentid = series["id"]
			content.append((title, image, contentid))
		return content

	def listCategories(self, formatId):
		content = [(_("Return back..."), None, "back")]
		detailed = self.api.detailed(formatId)
		for category in detailed["formatcategories"]:
			name = category["name"].encode("utf-8")
			image = str(mobileapi.IMAGE_URL % category["image"].replace(" ", "%20"))
			contentid = category["id"]
			content.append((name, image, contentid))
		return content

	def listVideos(self, category):
		content = [(_("Return back..."), None, "back")]
		videos = self.api.getVideos(category)
		for video in videos:
			title = video["title"].encode("utf-8")
			image = str(mobileapi.IMAGE_URL % video["image"].replace(" ", "%20"))
			hlspath = str(video["hlspath"])
			content.append((title, image, hlspath))
		return content


class TV3PlayMenu(Screen):
	skin = """
		<screen position="center,center" size="630,370">
			<eLabel position="5,0" size="620,2" backgroundColor="#aaaaaa" />
			<widget source="list" render="Listbox" position="10,15" size="360,300" \
				scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent" >
				{
					"template": [MultiContentEntryText(pos=(10, 1), size=(340, 30), \
							font=0, flags=RT_HALIGN_LEFT, text=0)],
					"fonts": [gFont("Regular", 20)],
					"itemHeight": 30
				}
				</convert>
			</widget>
			<widget name="pic" position="380,15" size="250,141" alphatest="on" />
			<widget name="cur" position="380,160" size="250,160" halign="center" font="Regular;22" />
			<eLabel position="110,358" size="148,2" backgroundColor="#00ff2525" />
			<eLabel position="370,358" size="148,2" backgroundColor="#00389416" />
			<widget source="key_red" render="Label" position="110,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
			<widget source="key_green" render="Label" position="370,328" zPosition="2" size="148,30" \
				valign="center" halign="center" font="Regular;22" transparent="1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("TV3 Play"))
		self.session = session
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Ok"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.Cancel,
				"ok": self.Ok,
				"green": self.Ok,
				"red": self.Cancel,
			})
		self["list"] = List([])
		self["list"].onSelectionChanged.append(self.SelectionChanged)
		self["pic"] = Pixmap()
		self["cur"] = Label()
		self.menulist = None
		self.categories = None
		self.defimage = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
			"Extensions/TV3Play/icon.png"))
		self.CreateRegions()
		if not os.path.exists(TMPDIR):
			os.mkdir(TMPDIR)
		self.onLayoutFinish.append(self.ShowDefPic)

	def CreateRegions(self):
		content = []
		for line in REGIONS:
			content.append((line, None, None))
		self["list"].setList(content)
		self["cur"].setText(content[0][0])

	def ShowDefPic(self):
		self["pic"].instance.setPixmap(self.defimage)

	def SelectionChanged(self):
		current = self["list"].getCurrent()
		if current[2] == "back":
			self["cur"].setText("")
			self.ShowDefPic()
		else:
			data = current[0]
			self["cur"].setText(data)
			imagepath = os.path.join(TMPDIR, data + ".jpg")
			if os.path.exists(imagepath) and os.path.getsize(imagepath) > 15000:
				sc = AVSwitch().getFramebufferScale()
				self.picload = ePicLoad()
				self.picload.PictureData.get().append(boundFunction(self.ShowPic))
				self.picload.setPara((self["pic"].instance.size().width(),
					self["pic"].instance.size().height(),
					sc[0], sc[1], False, 0, "#00000000"))
				self.picload.startDecode(imagepath)
			else:
				self.ShowDefPic()

	def ShowPic(self, picInfo = None):
		ptr = self.picload.getData()
		if ptr:
			print "[TV3 Play] Show image"
			self["pic"].instance.setPixmap(ptr.__deref__())
		del self.picload

	def Ok(self):
		current = self["list"].getCurrent()
		data = current[2]
		if data == "back":
			if self.menulist == "videos":
				content = (TV3PlayAddon(self.region).listCategories(self.categories))
				self.menulist = "categories"
			elif self.menulist == "categories":
				content = (TV3PlayAddon(self.region).listPrograms())
				self.menulist = "programs"
			else:
				content = []
				self.menulist = None
				self.CreateRegions()
		else:
			if not self.menulist:
				self.region = current[0]
				content = (TV3PlayAddon(self.region).listPrograms())
				self.menulist = "programs"
			elif self.menulist == "programs":
				content = (TV3PlayAddon(self.region).listCategories(data))
				self.menulist = "categories"
				self.categories = data
			elif self.menulist == "categories":
				content = (TV3PlayAddon(self.region).listVideos(data))
				self.menulist = "videos"
			else:
				content = []
				self.playVideo(data)
		if content:
			self["list"].setList(content)
			self["cur"].setText("")
			for line in content[1:]:
				image = os.path.join(TMPDIR, line[0] + ".jpg")
				if not os.path.exists(image):
					downloadPage(line[1], image)
			print "[TV3 Play] Images downloaded"

	def playVideo(self, videoId):
		if "tv3latviavod" in videoId:
			url1 = videoId.split("_definst_/", 1)
			url1 = url1[1].split(".mp4", 1)
			url = "rtmp://tv3latviavod.deac.lv/vod//mp4:" + url1[0]
		else:
			url = videoId
		ref = eServiceReference(4097, 0, url)
		mp = self.OpenMP()
		mp.playlist.addFile(ref)
		print "[TV3 Play] PLAY", url
		mp.playServiceRefEntry(ref)
		mp.playlist.updateList()
		playList = mp.playlist.getServiceRefList()
		for i in range(0, len(playList)):
			if playList[i] == ref:
				mp.playlist.deleteFile(i)
				mp.playlist.updateList()
				break

	def OpenMP(self):
		if hasattr(self.session, "mediaplayer"):
			mp = self.session.mediaplayer
			try:
				len(mp.playlist)
			except Exception, e:
				pass
			else:
				return mp
		if isinstance(self.session.current_dialog, MediaPlayer):
			self.session.mediaplayer = self.session.current_dialog
		else:
			self.session.mediaplayer = self.session.open(MediaPlayer)
		return self.session.mediaplayer

	def Cancel(self):
		if os.path.exists(TMPDIR):
			for name in os.listdir(TMPDIR):
				os.remove(os.path.join(TMPDIR, name))
			os.rmdir(TMPDIR)
		self.close()

