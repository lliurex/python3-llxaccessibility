#!/usr/bin/python3
import dbus,dbus.exceptions
from PySide2.QtGui import QClipboard
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QThread,Signal
import llxaccessibility.libs.a11Manager as a11Manager

class _klipperManager(QThread):
	def __init__(self,dbusInterface,parent=None,*args,**kwargs):
		super().__init__()
		self.dbusInterface=dbusInterface
	#def __init__

	def run(self):
		contents=self._getKlipperContents()
		self.clearKlipperContents()
		if len(contents)>0:
			contents.reverse()
			contents.pop()
			for item in contents:
				print(item)
				self.dbusInterface.setClipboardContents(item)
	#def run

	def _getKlipperItem(self,idx):
		item=self.dbusInterface.getClipboardHistoryItem(idx)
		return(item)
	#def _getKlipperItem

	def _getKlipperContents(self):
		contents=self.dbusInterface.getClipboardHistoryMenu()
		return(contents)
	#def _getKlipperContents

	def clearKlipperContents(self):
		contents=self.dbusInterface.clearClipboardContents()
		return(contents)
	#def clearKlipperContents

	def _clearKlipperhistory(self):
		contents=self.dbusInterface.clearClipboardHistory()
		return(contents)
	#def _clearKlipperHistory
#class _klipperManager

class clipboardManager():
	def __init__(self,*args,**kwargs):
		try:
			dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		except:
			pass
		if QApplication.instance()==None:
			app=QApplication(["clipman"])
		try:
			dbusObj=dbus.SessionBus()
		except Exception as e:
			print(e)
			dbusObj=None
		self.dbusInterface=None
		if dbusObj!=None:
			dbusObject=dbusObj.get_object("org.kde.klipper","/klipper")
			self.dbusInterface=dbus.Interface(dbusObject,"org.kde.klipper.klipper")
		self.klipper=_klipperManager(self.dbusInterface)
		self.clipboard=QClipboard()
		self.a11Manager=a11Manager.a11Manager()
	#def __init__(self,*args,**kwargs):

	def getContents(self):
		item=b''
		if self.dbusInterface!=None:
			item=self.klipper._getKlipperItem(0)
			if item!=None:
				item=item.encode()
			else:
				item=b''
		if item.isascii()==False:
			item=self._getClipboardImage()
		else:
			item=item.decode("utf8")
		return(item)
	#def getContents

	def popContentsAsync(self):
		self.klipper.start()
	#def _clearKlipperContents(self):

	def getClipboardContents(self):
		content=self._getClipboardImage()
		if content.isNull():
			content=self._getClipboardText()
		return(content)
	#def getClipboardContents

	def _clearClipboardContents(self):
		pass
	#def _clearClipboardContents

	def _getClipboardImage(self,mode=QClipboard.Selection):
		img=self.clipboard.image(mode)
		if img.isNull()==False:
			img=self.clipboard.pixmap(mode)
		return(img)
	#def getImage

	def popClipboard(self,mode=QClipboard.Selection):
		content=self._getClipboardContents()
		self.clipboard.setText("")
		return(content)

	def _getClipboardText(self):
		txt=""
		print(self.clipboard.ownsSelection())
		clipboard=QClipboard()
		txt=clipboard.text(self.clipboard.Selection)
		txt=txt.strip()
		if len(txt)==0:
			self.a11Manager.selectAll()
			txt=clipboard.text(self.clipboard.Selection).strip()
		if len(txt)!=0:
			print("DELETE")
			self.clipboard.clear(self.clipboard.Selection)
			self.clipboard.clear(self.clipboard.Clipboard)
		#	self.klipper.clearKlipperContents()
		#if not txt:
		#	txt=self.clipboard.text()
		return(txt)
	#def _getClipboardText

