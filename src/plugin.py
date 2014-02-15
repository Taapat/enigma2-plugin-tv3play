from Plugins.Plugin import PluginDescriptor

from . import _


def main(session, **kwargs):
	from TV3Play import TV3PlayMenu
	session.open(TV3PlayMenu)

def Plugins(**kwargs):
	return [PluginDescriptor(name = _("TV3 Play"),
		description = _("Watch TV3 play online services"),
		where = [PluginDescriptor.WHERE_PLUGINMENU,
		PluginDescriptor.WHERE_EXTENSIONSMENU],
		icon = "picon.png", fnc = main)]
