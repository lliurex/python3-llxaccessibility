#!/usr/bin/python
import dbus,dbus.exceptions
import os
from . import kconfig
class manager():
	def __init__(self,parent=None):
		self.dbg=False
		self.kconfig=kconfig.kconfig()
		self.bus=None
	#def __init__

	def getKWinEffects(self):
		paths=["/usr/share/kwin/builtin-effects","/usr/share/kwin/effects",os.path.join(os.getenv("HOME"),".local","share","kwin","effects")]
		effects={}
		added=[]
		for i in paths:
			if os.path.exists(i):
				for effect in os.scandir(i):
					data=self.kconfig.readMetadata(effect.path)
					if len(data)>0:
						if "KPackageStructure" not in data:
							data["KPackageStructure"]="KWin/Effect"
						effects.update({effect.name:data})
						if "KPlugin" in data:
							kid=data["KPlugin"]["Id"]
							added.append(kid)
							if kid.startswith("kwin4_effect_")==False:
								added.append("kwin4_effect_{}".format(kid))
		for keffect in self._getDbusKWinEffects():
			if str(keffect) not in added:
				name=keffect.replace("kwin4_effect_","").capitalize()
				data={}
				data["KPackageStructure"]="KWin/Effect"
				data['KPlugin']={'Category':'Appearance', 'Description':name,'Id':keffect,'License': 'GPL', 'Name':name}
				data['path']=''
				effects.update({name:data})
				added.append(keffect)
		return(effects)
	#def getKWinEffects

	def _getDbusKWinEffects(self):
		if self.bus==None:
			self._connectBus()
		dKwin=self.bus.get_object("org.kde.KWin","/Effects")
		effects=dKwin.Get("org.kde.kwin.Effects","listOfEffects",dbus_interface="org.freedesktop.DBus.Properties")
		return(effects)
	#def _getDbusEffectsForKWin

	def getKWinScripts(self):
		paths=["/usr/share/kwin/scripts",os.path.join(os.getenv("HOME"),".local","share","kwin","scripts")]
		scripts={}
		for i in paths:
			if os.path.exists(i):
				for script in os.scandir(i):
					data=self.kconfig.readMetadata(script.path)
					scripts.update({script.name:data})
		return(scripts)
	#def getKWinScripts

	def getKWinPlugins(self,categories=["Accessibility"]):
		plugins={}
		plugins.update(self.getKWinEffects())
		plugins.update(self.getKWinScripts())
		if len(categories)>0:
			filteredplugins={}
			for plugin,data in plugins.items():
				if len(data)==0 or "KPackageStructure" not in data:
					continue
				if data["KPackageStructure"]=="KWin/Effect":
					if data["KPlugin"].get("Category") in categories:
						filteredplugins.update({plugin:data})
				else:
					filteredplugins.update({plugin:data})
			plugins=filteredplugins.copy()
		return(plugins)
	#def getKWinPlugins

	def getPluginEnabled(self,plugin):
		enabled=False
		(dKwin,dInt)=self._getDbusInterfaceForPlugin(plugin)
		if dKwin==None or dInt==None:
			return
		plugid=plugin.get("KPlugin",{}).get("Id","")
		if "Script" in plugin.get("KPackageStructure",""):
			if dKwin.isScriptLoaded(plugid)==1:
				enabled=True
		else:
			if dKwin.isEffectLoaded(plugid)==1:
				enabled=True
		return(enabled)
	#def getPluginEnabled

	def togglePlugin(self,plugin):
		enabled=False
		(dKwin,dInt)=self._getDbusInterfaceForPlugin(plugin)
		if dKwin==None or dInt==None:
			return
		plugid=plugin.get("KPlugin",{}).get("Id","")
		if plugin.get("KPackageStructure","")=="KWin/Script":
			if dKwin.isScriptLoaded(plugid)==0:
				enabled=True
			self.kconfig.writeKFile("kwinrc","Plugins","{}Enabled".format(plugid),str(enabled).lower())
			self._debug("Script {} enabled: {}".format(plugid,enabled))
			self.applyKWinChanges()
		else:
			dKwin.toggleEffect(plugid)
			if dKwin.isEffectLoaded(plugid)==1:
				enabled=True
			self._debug("Effect {} enabled: {}".format(plugid,enabled))
		return(enabled)
	#def togglePlugin

	def applyKWinChanges(self):
		if self.bus==None:
			self._connectBus()
		dobject="/KWin"
		dKwin=self.bus.get_object("org.kde.KWin",dobject)
		self._debug("Reloading kwin")
		dKwin.reconfigure()
	#def applyKWinChanges


	def _getDbusInterfaceForPlugin(self,plugin):
		plugtype=plugin.get("KPackageStructure","")
		dwin=None
		dinterface=None
		if len(plugtype)>0:
			plugid=plugin.get("KPlugin",{}).get("Id","")
			if self.bus==None:
				self._connectBus()
			if "Script" in plugtype:
				dobject="/Scripting"
				dinterface="org.kde.kwin.Scripting"
			else:
				dobject="/Effects"
				dinterface="org.kde.kwin.Effects"
			try:
				dwin=self.bus.get_object("org.kde.KWin",dobject)
			except Exception as e:
				print("Could not connect to bus: %s\nAborting"%e)
				sys.exit(1)
		return(dwin,dinterface)
	#def _getDbusInterfaceForPlugin

	def _connectBus(self):
		try:
			self.bus=dbus.SessionBus()
		except Exception as e:
			print("Could not get session bus: %s\nAborting"%e)
			sys.exit(1)
	#def _connectBus

#class kwinManager
