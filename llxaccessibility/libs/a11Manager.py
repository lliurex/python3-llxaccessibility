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
		self.register=pyatspi.Registry()
		self.oldComponent=None
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
						break
				try:
					if window.getState().contains(pyatspi.STATE_ACTIVE):
						break
				except Exception as e:
					pass
			if component!=None:
				break
		return window
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
		pyatspi.Registry.registerEventListener(self._emitStateFocused, "object:state-changed:focused")
		pyatspi.Registry.registerEventListener(self._emitStateChanged,
		#							'object:state-changed:focused')
					#				'object:state-changed:showing',
									'object:state-changed:active',)
		#							'object:state-changed:selected')
		pyatspi.Registry.registerEventListener(self._emitStateSelected, "object:state-changed:selected")
		pyatspi.Registry.start()
		self._debug("Bring up registry")

	def trackFocus(self,callback,oneshot=False):
		self._debug("Tracking focus")
		self.callback=callback
		self._debug("Setting up registry")
		self.procTrackFocus=threading.Thread(target=self._thTrackFocus,args=[callback])
		self.procTrackFocus.start()
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
		#	self._debug("INSPECTING WINDOW {} {}".format(index,root))
			if root.getState().contains(pyatspi.STATE_FOCUSED) and root.getState().contains(pyatspi.STATE_SHOWING):
				self._debug("root found")
				focused=root
				compfocused=None
				for tree in focused:
					compfocused=inspectTree(index + 1, tree)
					if compfocused!=None:
						break
				if compfocused!=None:
					focused=compfocused
						
				self._debug(root)
			else:
				for tree in root:
					focused=inspectTree(index + 1, tree)
		#			self._debug("F: {}".format(focused))
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

	def _emitStateSelected(self,event):
		self._debug("SELECTED")
		component=event.source
		if component==self.oldComponent:
			return
		self.oldComponent=component
		name=""
		data={"component":"","x":-1,"y":-1,"w":0,"h":0}
		try:
			if component.getState().contains(pyatspi.STATE_SELECTED) and component.getState().contains(pyatspi.STATE_SHOWING):
				name=component.name
		except Exception as e:
			self._debug("focusErr:{} {}".format(component,e))
			return
		if name=="":
			self._debug(" -> no name")
			return
			position=component.get_position(pyatspi.component.XY_SCREEN)
			size=component.get_size()
			data=self.getCurrentFocusCoords()
		else:
			self._debug("Name: {}".format(name))
			size=component.get_size()
			position=component.get_position(pyatspi.component.XY_SCREEN)
			#data=self.getCurrentFocusCoords()
			data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		return(self.callback(data))
	#	self._emitStateFocused(event)

	def _emitStateChanged(self,event):
		self._debug("CHANGED")
		component=event.source
		if component==self.oldComponent:
			return
		self.oldComponent=component
		name=""
		data={"component":"","x":-1,"y":-1,"w":0,"h":0}
		try:
			if component.getState().contains(pyatspi.STATE_ACTIVE) and component.getState().contains(pyatspi.STATE_SHOWING):
				name=component.name
		except Exception as e:
			self._debug("focusErr:{} {}".format(component,e))
			return
		if name=="":
			self._debug(" -> no name")
			return
			position=component.get_position(pyatspi.component.XY_SCREEN)
			size=component.get_size()
			data=self.getCurrentFocusCoords()
		else:
			self._debug("Name: {}".format(name))
			size=component.get_size()
			position=component.get_position(pyatspi.component.XY_SCREEN)
			#data=self.getCurrentFocusCoords()
			data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		self._debug(data)
		return(self.callback(data))
		#print(self.getCurrentFocusCoords())
		#self._emitStateFocused(event)

	def _emitStateFocused(self,event):
		self._debug("ACTIVE")
		component=event.source
		if component==self.oldComponent:
			return
		self.oldComponent=component
		name=""
		data={"component":"","x":-1,"y":-1,"w":0,"h":0}
		try:
			if component.getState().contains(pyatspi.STATE_FOCUSED) and component.getState().contains(pyatspi.STATE_SHOWING):
				name=component.name
		except Exception as e:
			print("focusErr:{} {}".format(component,e))
			return
		if name=="":
			self._debug(" -> no name")
			data=self.getCurrentFocusCoords()
		else:
			self._debug("Name: {}".format(name))
			size=component.get_size()
			position=component.get_position(pyatspi.component.XY_SCREEN)
			#data=self.getCurrentFocusCoords()
			data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		self.untrackFocus()
		self._debug(data)
		self._debug("--")
		return(self.callback(data))
		#self.register.stop()
		#self.procTrackFocus.join()
		#self.register.start()
		#print("exited")
	#def _emitFocusChanged
#class a11Manager

