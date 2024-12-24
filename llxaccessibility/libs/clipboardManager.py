#!/usr/bin/python3
from PySide2.QtGui import QClipboard

class clipboardManager():
	def __init__(self,*args,**kwargs):
		self.bus=True
		try:
			self.bus=dbus.Bus()
		except Exception as e:
			self.bus=False
	#def __init__(self,*args,**kwargs):

	def test(self):
		try:
			dbusObject=self.bus.get_object("org.kde.klipper","/klipper")
			dbusInterface=dbus.Interface(dbusObject,"org.kde.klipper.klipper")
		except:
			pass
	#def test

	def getContents(self):
		if self.bus==True:
			return(self._getKlipperContents())
		else:
			return(self._getClipboardContents())
	#def getContents

	def clearContents(self):
		if self.bus==True:
			return(self._clearKlipperContents())
		else:
			return(self._clearClipboardContents())

	def _getKlipperContents(self):
		dbusObject=self.bus.get_object("org.kde.klipper","/klipper")
		dbusInterface=dbus.Interface(dbusObject,"org.kde.klipper.klipper")
		contents=dbusInterface.getClipboardContents()
		return(contents)
	#def _getKlipperContents(self):

	def _clearKlipperContents(self):
		dbusObject=self.bus.get_object("org.kde.klipper","/klipper")
		dbusInterface=dbus.Interface(dbusObject,"org.kde.klipper.klipper")
		contents=dbusInterface.setClipboardContents(" ")
		return(contents)
	#def _clearKlipperContents(self):

	def _getClipboardContents(self):
		pass
	#def _getClipboardContents

	def _clearClipboardContents(self):
		pass
	#def _clearClipboardContents

