import pyatspi,os
import time
import threading

keys={"CTRL":105,
	"a":38,
	"c":54,
	"4":13
	}

class a11Manager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("a11Manager: {}".format(msg))
	#def _debug

	def activeWindow(self):
		desktops=pyatspi.Registry.getDesktopCount()
		component=None
		for idx in range(0,desktops):
			desktop = pyatspi.Registry.getDesktop(idx)
			for app in desktop:
				for window in app:
					if window.getState().contains(pyatspi.STATE_ACTIVE):
						component=window[-1]
				try:
					if window.getState().contains(pyatspi.STATE_ACTIVE):
						break
				except Exception as e:
					pass
			if component!=None:
				break
		print("CM: {}".format(component))
		print("AC: {}".format(app))
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

	def _thTrackFocus(self,callback):
		register=pyatspi.Registry()
		register.registerEventListener(self._emitFocusChanged, "object:state-changed:focused")
		register.registerEventListener(self._emitFocusChanged, "object:state-changed:selected")
		register.start()
		self._debug("Bring up registry")

	def trackFocus(self,callback,oneshot=False):
		self._debug("Tracking focus")
		self.callback=callback
		self._debug("Setting up registry")
		proc=threading.Thread(target=self._thTrackFocus,args=[callback])
		proc.start()
		self._debug("Tracking focus ENABLED")
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
			else:
				for tree in root:
					focused=inspectTree(index + 1, tree)
					if focused!=None:
						break
			return(focused)
		data={"position":0,"x":0,"y":0,"size":0,"w":0,"h":0}
		focused=inspectTree(0, self.activeWindow())
		if focused==None:
			focused=self.activeWindow()
		position=focused.get_position(pyatspi.component.XY_SCREEN)
		size=focused.get_size()
		data={"position":-1,"x":position.x,"y":position.y,"size":-1,"w":size.x,"h":size.y}
		return(data)
	#def getCurrentFocusCoords

	def _emitFocusChanged(self,event):
		component=event.source
		try:
			name=component.name
			position=component.get_position(pyatspi.component.XY_SCREEN)
		except Exception as e:
			print("focusErr: {}".format(e))
			return
		size=component.get_size()
		data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		return(self.callback(data))
	#def _emitFocusChanged
#class a11Manager

