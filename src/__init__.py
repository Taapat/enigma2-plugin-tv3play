from gettext import bindtextdomain, dgettext, gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


def localeInit():
	bindtextdomain("TV3Play", resolveFilename(SCOPE_PLUGINS, \
		"Extensions/TV3Play/locale"))


def _(txt):
	t = dgettext("TV3Play", txt)
	if t == txt:
		t = gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

