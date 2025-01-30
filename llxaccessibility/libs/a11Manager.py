import pyatspi,threading,signal,sys
import time
import threading
import dbus,dbus.service,dbus.exceptions
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

keys={"CTRL":105,
	"a":38,
	"c":54,
	"4":13
	}

class dbusMethods(dbus.service.Object):
	def __init__(self,bus_name,*args,**kwargs):
		super().__init__(bus_name,"/net/lliurex/accessibility")
		self.dbg=True
		self.eventManager=eventManager(*args,**kwargs)
		self.eventManager.focusTrack(self.focusChangedSignal,False)
	#def __init__

	def focusChangedSignal(self,*args,**kwargs):
		self.focusChanged(str(args[0]))
	#def _updatedSignal

	@dbus.service.signal("net.lliurex.accessibility")
	def focusChanged(self,*args,**kwargs):
		pass
	#def focusChanged

	@dbus.service.method("net.lliurex.accessibility",
						 in_signature='', out_signature='s')
	def getCurrentFocusCoords(self):
		return(self.eventManager.getCurrentFocusCoords())

class eventManager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
		if len(args)>0:
			self.callback=args[0]
		elif kwargs.get("callback",None)!=None:
			self.callback=kwargs["callback"]
		else:
			self.callback=print
		if len(args)>1:
			self.oneshot=args[1]
		elif kwargs.get("oneshot",None)!=None:
			self.oneshot=kwargs["oneshot"]
		else:
			self.oneshot=False
		if len(args)>2:
			self.DbusMethods=args[2]
		elif kwargs.get("dbus",None)!=None:
			self.DBusMethods=kwargs["dbus"]
		else:
			self.DBusMethods=None
		
		self.atspi=pyatspi
		self.register=self._startListener()
	#def __init__

	def _startListener(self):
		register=self.atspi.Registry()
		register.registerEventListener(self.processEvent, "object:state-changed:focused")
		register.registerEventListener(self.processEvent, "object:state-changed:selected")
		return(register)
	#def _startListener(self):

	def processEvent(self,event):
		component=event.source
		try:
			name=component.name
			position=component.get_position(self.atspi.XY_SCREEN)
		except:
			return
		size=component.get_size()
		data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		if self.oneshot==True:
			self.register.stop()
		if self.DBusMethods!=None:
			self.DBusMethods.focusChangedSignal(data)
		if self.callback!=None:
			self.callback(data)
	#def processEvent

	def focusTrack(self,callback,oneshot):
		self.callback=callback
		self.oneshot=oneshot
		try:
			self.register.start()
		except:
			self.register=pyatspi.Registry()
			self.register.registerEventListener(self.processEvent, "object:state-changed:focused")
			self.register.start()
	#def focusChanged
#class eventManager

class a11Manager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("a11Manager: {}".format(msg))
	#def _debug

	def _setDBus(self):
		DBusGMainLoop(set_as_default=True)
		loop = GLib.MainLoop()
		# Declare a name where our service can be reached
		try:
			bus_name = dbus.service.BusName("net.lliurex.accessibility",
											bus=dbus.SessionBus(),
											do_not_queue=True)
		except dbus.exceptions.NameExistsException:
			print("service is already running")
		else:
			self.DBusMethods=dbusMethods(bus_name)
			# Run the loop
			try:
				self._debug("D-Bus started")
				loop.run()
			except KeyboardInterrupt:
				print("keyboard interrupt received")
			except Exception as e:
				print("Unexpected exception occurred: '{}'".format(str(e)))
			finally:
				loop.quit()
	#def _setDBus

	def activeWindow(self):
		idx=pyatspi.Registry.getDesktopCount()
		desktop = pyatspi.Registry.getDesktop(0)
		for app in desktop:
			for window in app:
				if window.getState().contains(pyatspi.STATE_ACTIVE):
					for component in window:
						break
			try:
				if window.getState().contains(pyatspi.STATE_ACTIVE):
					break
			except Exception as e:
				pass
		return app
	#def activeWindow

	def selectAll(self):
		time.sleep(1)
		app=self.activeWindow()
		with open("/tmp/a","w") as f:
			f.write("{}\n".format(app))
		if app!=None:
			chld=app.getChildAtIndex(0).getChildAtIndex(0)
			if chld==None:
				chld=app.getChildAtIndex(0)
			chld.queryComponent().grabFocus()
			#Set selection mode for okular
			if "okular" in app.get_name().lower():
				pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
				pyatspi.Registry.generateKeyboardEvent(keys["4"], None, pyatspi.KEY_PRESSRELEASE)
				pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
			pyatspi.Registry.generateKeyboardEvent(keys["a"], None, pyatspi.KEY_PRESSRELEASE)
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
			#time.sleep(0.1)
#			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
#			pyatspi.Registry.generateKeyboardEvent(keys["c"], None, pyatspi.KEY_PRESSRELEASE)
#			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
		return
	#def selectAll

	def trackFocus(self,callback,oneshot=False):
		#self.eventManager.focusChanged(callback,oneshot,self.DBusMethods)
		self._debug("D-Bus starting")
		self.proc=threading.Thread(target=self._setDBus)
		self.proc.start()
		return
	#def trackFocus

	def untrackFocus(self):
		pyatspi.Registry.stop()
		return
	#def untrackFocus

	def getCurrentFocusCoords(self):
		def inspectTree(index,root):
			focused=None
			if root.getState().contains(pyatspi.STATE_FOCUSED) and root.getState().contains(pyatspi.STATE_SHOWING):
				focused=root
			for tree in root:
				focused=inspectTree(index + 1, tree)
				if focused!=None:
					break
			return(focused)
		data={"position":0,"x":0,"y":0,"size":0,"w":0,"h":0}
		focused=inspectTree(0, self.activeWindow())
		if focused!=None:
			position=focused.get_position(pyatspi.component.XY_SCREEN)
			size=focused.get_size()
			data={"position":"NULL","x":position.x,"y":position.y,"size":"NULL","w":size.x,"h":size.y}
		return(data)
	#def getCurrentFocusCoords

	def _emitFocusChanged(self,event):
		component=event.source
		position=component.get_position(pyatspi.component.XY_WINDOW)
		size=component.get_size()
		data={"position":position,"x":position.x,"y":position.y,"size":size,"w":size.x,"h":size.y}
		self.dBusMethods.focusChangedSignal(data)
		#callback(data)
		return
	#def _emitFocusChanged
#class a11Manager

