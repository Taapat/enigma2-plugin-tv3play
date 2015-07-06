import os
from twisted.web.client import downloadPage

from enigma import ePicLoad, eServiceReference, eTimer
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

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


class TV3Player(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def leavePlayer(self):
		self.session.openWithCallback(self.leavePlayerConfirmed,
			MessageBox, _("Stop playing?"))

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.close()

	def doEofInternal(self, playing):
		pass

	def getPluginList(self):
		from Components.PluginComponent import plugins
		list = []
		for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != _("TV3 Play"):
				list.append(((boundFunction(self.getPluginName, p.name),
					boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass


class TV3PlayAddon(object):
	def __init__(self, region):
		self.region = region
		self.api = mobileapi.TV3PlayMobileApi(region)

	def listPrograms(self):
		content = [(_("Return back..."), None, "back")]
		formats = self.api.getAllFormats()
		if " Error " in formats:
			return " Error " + formats[" Error "]
		for series in formats:
			title = series["title"].encode("utf-8")
			image = str(mobileapi.IMAGE_URL % series["image"].replace(" ", "%20"))
			contentid = series["id"]
			content.append((title, image, contentid))
		return content

	def listCategories(self, formatId):
		content = [(_("Return back..."), None, "back")]
		detailed = self.api.detailed(formatId)
		if " Error " in detailed:
			return " Error " + detailed[" Error "]
		for category in detailed["formatcategories"]:
			name = category["name"].encode("utf-8")
			image = str(mobileapi.IMAGE_URL % category["image"].replace(" ", "%20"))
			contentid = category["id"]
			content.append((name, image, contentid))
		return content

	def listVideos(self, category):
		content = [(_("Return back..."), None, "back")]
		videos = self.api.getVideos(category)
		if " Error " in videos:
			return " Error " + videos[" Error "]
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
		self.storedcontent = {}
		self.picloads = {}
		self.defimage = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
			"Extensions/TV3Play/icon.png"))
		self.spinstarted = 0
		self.spinner = {}
		self.spinnerTimer = eTimer()
		self.spinnerTimer.callback.append(self.SelectionChanged)
		if not os.path.exists(TMPDIR):
			os.mkdir(TMPDIR)
		self.onLayoutFinish.append(self.LayoutFinish)

	def LayoutFinish(self):
		for data in range(1, 8):
			self.spinner[data] = LoadPixmap(resolveFilename(SCOPE_PLUGINS,
			"Extensions/TV3Play/wait%s.png" % data))
		content = []
		for data in REGIONS:
			content.append((data, None, None))
			image = os.path.join(TMPDIR, data + ".jpg")
			self.picloads[image] = False
		self["list"].setList(content)
		self["cur"].setText(content[0][0])
		self.storedcontent["regions"] = content
		self.ShowDefPic()

	def StartSpinner(self):
		if self.spinstarted == 0:
			self.spinnerTimer.start(300, False)
		self.spinstarted += 1
		if self.spinstarted == 8:
			self.spinstarted = 1
		self["pic"].instance.setPixmap(self.spinner[self.spinstarted])

	def StopSpinner(self):
		if self.spinstarted > 0:
			self.spinstarted = 0
			self.spinnerTimer.stop()

	def ShowDefPic(self):
		self["pic"].instance.setPixmap(self.defimage)

	def SelectionChanged(self):
		current = self["list"].getCurrent()
		if current[2] == "back":
			self["cur"].setText("")
			self.StopSpinner()
			self.ShowDefPic()
		else:
			data = current[0]
			self["cur"].setText(data)
			image = os.path.join(TMPDIR, data + ".jpg")
			if image in self.picloads:
				self.StopSpinner()
				if self.picloads[image] is True:
					self.DecodePic(image)
				else:
					self.ShowDefPic()
			else:
				self.StartSpinner()

	def DecodePic(self, image):
		sc = AVSwitch().getFramebufferScale()
		self.picloads[image] = ePicLoad()
		self.picloads[image].PictureData.get().append(boundFunction(self.FinishDecode, image))
		self.picloads[image].setPara((self["pic"].instance.size().width(),
			self["pic"].instance.size().height(),
			sc[0], sc[1], False, 0, "#00000000"))
		self.picloads[image].startDecode(image)

	def FinishDecode(self, image, picInfo = None):
		ptr = self.picloads[image].getData()
		if ptr:
			self["pic"].instance.setPixmap(ptr.__deref__())
			del self.picloads[image]
			self.picloads[image] = True

	def Ok(self):
		current = self["list"].getCurrent()
		content = self.getContent(current)
		if content:
			self["list"].setList(content)
			self["cur"].setText("")
			for line in content[1:]:
				image = os.path.join(TMPDIR, line[0] + ".jpg")
				if not image in self.picloads:
					downloadPage(line[1], image)\
						.addCallback(boundFunction(self.downloadFinished, image))\
						.addErrback(boundFunction(self.downloadFailed, image))

	def downloadFinished(self, image, result):
		self.picloads[image] = True

	def downloadFailed(self, image, result):
		self.picloads[image] = False

	def getContent(self, current):
		data = current[2]
		print "[TV3 Play] Select:", data
		if data == "back":
			if self.menulist == "videos":
				stored = "categories%s" % self.categories
				content = self.storedcontent[stored]
				self.menulist = "categories"
			elif self.menulist == "categories":
				stored = "programs%s" % self.region
				content = self.storedcontent[stored]
				self.menulist = "programs"
			else:
				content = self.storedcontent["regions"]
				self.menulist = None
		else:
			if not self.menulist:
				self.region = current[0]
				stored = "programs%s" % self.region
				if stored in self.storedcontent:
					content = self.storedcontent[stored]
				else:
					content = (TV3PlayAddon(self.region).listPrograms())
					if self.isError(content):
						return None
					self.storedcontent[stored] = content
				self.menulist = "programs"
			elif self.menulist == "programs":
				stored = "categories%s" % data
				if stored in self.storedcontent:
					content = self.storedcontent[stored]
				else:
					content = (TV3PlayAddon(self.region).listCategories(data))
					if self.isError(content):
						return None
					self.categories = data
					self.storedcontent["categories%s" % data] = content
				self.menulist = "categories"
			elif self.menulist == "categories":
				stored = "videos%s" % data
				if stored in self.storedcontent:
					content = self.storedcontent[stored]
				else:
					content = (TV3PlayAddon(self.region).listVideos(data))
					if self.isError(content):
						return None
					self.videos = data
					self.storedcontent["videos%s" % data] = content
				self.menulist = "videos"
			else:
				content = None
				self.playVideo(current)
		return content

	def isError(self, content):
		if content[:7] == " Error ":
			self.session.open(MessageBox, content, MessageBox.TYPE_INFO)
			return True
		else:
			return False

	def playVideo(self, current):
		#if "tv3latviavod" in videoId:
			#url = videoId.split("_definst_/", 1)[1].split("/playlist.m3", 1)
			#videoId = "rtmp://tv3latviavod.deac.lv/vod//mp4:" + url[0]
		ref = eServiceReference(4097, 0, current[2])
		ref.setName(current[0])
		print "[TV3 Play] Play:", current[2]
		self.session.open(TV3Player, ref)

	def Cancel(self):
		if os.path.exists(TMPDIR):
			for name in os.listdir(TMPDIR):
				os.remove(os.path.join(TMPDIR, name))
			os.rmdir(TMPDIR)
		self.close()

