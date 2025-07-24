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
		self.oldData=None
		self.focused=False
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("a11Manager: {}".format(msg))
	#def _debug

	def selectedWindow(self):
		desktops=pyatspi.Registry.getDesktopCount()
		component=None
		window=None
		for idx in range(0,desktops):
			desktop = pyatspi.Registry.getDesktop(idx)
			for app in desktop:
				for windows in app:
					for window in windows:
						if window==None:
							continue
						if window.getState().contains(pyatspi.STATE_SELECTED):
							component=window
							print("poer {}".format(component.role))
							break
				if component!=None:
					break
			if component!=None:
				print("SELECTED: {}".format(component.get_position(pyatspi.component.XY_SCREEN).y))
				break
		return component
	#def activeWindow

	def activeWindow(self):
		desktops=pyatspi.Registry.getDesktopCount()
		component=None
		window=None
		for idx in range(0,desktops):
			desktop = pyatspi.Registry.getDesktop(idx)
			for app in desktop:
				for window in app:
					if window.getState().contains(pyatspi.STATE_FOCUSED) and window.getState().contains(pyatspi.STATE_SHOWING):
						print("Active: {}".format(window))
						component=window[-1]
						break
				if component!=None:
						break
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
		pyatspi.Registry.registerEventListener(self._emitStateChanged,
		#							'object:state-changed:focused')
					#				'object:state-changed:showing',
									'object:state-changed:active',)
	#								'object:state-changed:selected')
		self.register.registerEventListener(self._emitStateSelected, "object:state-changed:selected")
	#	pyatspi.Registry.registerEventListener(self._emitStateFocused, "object:state-changed:focused")
		self.register.registerEventListener(self._emitStateFocused, "object:state-changed:focused")
		self.register.start()
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
		#pyatspi.Registry.stop()
		self.register.stop()
		return
	#def untrackFocus

	def getCurrentFocusCoords(self):
		def inspectTree(index,root):
			focused=None
		#	self._debug("INSPECTING WINDOW {} {}".format(index,root))
			states=root.getState()
			if (states.contains(pyatspi.STATE_FOCUSED) and states.contains(pyatspi.STATE_SHOWING)) and not(root.getRole()==pyatspi.ROLE_FILLER or states.contains(pyatspi.STATE_FOCUSABLE)):
				self._debug("root found: {}".format(root.getState().get_states()))
				role=root.getRole()
				self._debug("root found: {}".format(role.get_name(role)))
				focused=root
				compfocused=None
				for tree in focused:
					compfocused=inspectTree(index + 1, tree)
					if compfocused!=None:
						break
				if compfocused!=None:
					focused=compfocused
			elif not(root.getRole()==pyatspi.ROLE_FILLER or states.contains(pyatspi.STATE_FOCUSABLE)):
				for tree in root:
					focused=inspectTree(index + 1, tree)
					self._debug("F: {}".format(focused))
					if focused!=None:
						break
						
			self._debug("Find: {}".format(focused))
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
		self.register.stop()
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
			self._debug("Selected -> no name")
			#return
			position=component.get_position(pyatspi.component.XY_SCREEN)
			size=component.get_size()
		#	data=self.getCurrentFocusCoords()
		else:
			self._debug("Selected Name: {}".format(name))
			size=component.get_size()
			position=component.get_position(pyatspi.component.XY_SCREEN)
			#data=self.getCurrentFocusCoords()
		data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		if data==self.oldData:
			return
		self.oldData=data
		return(self.callback(data))
	#	self._emitStateFocused(event)

	def _emitStateChanged(self,event):
		self._debug("CHANGED")
		component=event.source
		#if component==self.oldComponent:
		#	return
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
			self._debug("Changed -> no name")
			return
			position=component.get_position(pyatspi.component.XY_SCREEN)
			size=component.get_size()
			data=self.getCurrentFocusCoords()
		else:
			self._debug("Changed Name: {}".format(name))
			size=component.get_size()
			position=component.get_position(pyatspi.component.XY_SCREEN)
			#data=self.getCurrentFocusCoords()
			data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		if data==self.oldData:
			return
		self.oldData=data
		self._debug(data)
		return(self.callback(data))
		#print(self.getCurrentFocusCoords())
		#self._emitStateFocused(event)

	def _emitStateFocused(self,event):
		self._debug("FOCUSED")
		component=event.source
		if component==self.oldComponent:
			return
		name=component.name
		fixedPositionX=0
		fixedPositionY=0
		data={"component":"","x":-1,"y":-1,"w":0,"h":0}
		try:
			if component.getState().contains(pyatspi.STATE_FOCUSED) and component.getState().contains(pyatspi.STATE_SHOWING):
				name=component.name
		except Exception as e:
			print("focusErr:{} {}".format(component,e))
		#Konsole has a bug, losing coords of component if comes frome a popup with a slash in the item menu description
		#Fix not found
		#if "popup" in str(component.parent):
		#	w=self.activeWindow()
		#	print("FO: {}".format(w.name))
		#	if "/" in str(component):
		#		print("HIT")
		#		popPosition=component.parent.get_position(pyatspi.component.XY_SCREEN)
		#		for itemMenu in component.parent:
		#			itemMenu.clear_cache()
		#			itemPosition=itemMenu.get_extents(pyatspi.component.XY_WINDOW)
		#			print(popPosition.y)
		#			print (itemPosition.y)
		if name=="":
			self._debug("Focused -> no name")
			self._debug("Focused -> no name {}".format(component.role))
			self._debug("Focused -> no name {}".format(component.parent))
			#data=self.getCurrentFocusCoords()
			name="unknown"
		else:
			self._debug("Active Name: {}".format(name))
			self._debug("Focused name {}".format(component.role))
			self._debug("Focused name {}".format(type(component.parent)))
		try:
			if component.queryAction().nActions<1:
				print("NO ACTION DETECTED")
				return
		except:
			pass
		for chld in component.parent:
			if chld.getState().contains(pyatspi.STATE_SHOWING):
				if chld.getState().contains(pyatspi.STATE_FOCUSED):
					print(chld)

		size=component.get_size()
		position=component.get_position(pyatspi.component.XY_SCREEN)
		data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
		parent=component.parent
		self.untrackFocus()
		#component.grab_focus()
		minX=position.x
		minY=position.y
		maxX=position.x+size.x
		maxY=position.y+size.y
		if component.parent.contains(minX,minY,pyatspi.component.XY_SCREEN)==False or component.parent.contains(maxX,maxY,pyatspi.component.XY_SCREEN)==False:
			print("I'M OUT!!")
			print("Old: {}".format(data))
			time.sleep(0.2)
			position=component.get_position(pyatspi.component.XY_SCREEN)
			data={"component":name,"x":position.x,"y":position.y,"w":size.x,"h":size.y}
			print("New: {}".format(data))
		
		if data==self.oldData:
			return
		self.oldData=data
		self.oldComponent=component
		return(self.callback(data))
		#self.register.stop()
		#self.procTrackFocus.join()
		#self.register.start()
		#print("exited")
	#def _emitFocusChanged
#class a11Manager

