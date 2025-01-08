import pyatspi
import time

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
		desktop = pyatspi.Registry.getDesktop(0)
		for app in desktop:
			for window in app:
				if window.getState().contains(pyatspi.STATE_ACTIVE):
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
			time.sleep(0.1)
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
			pyatspi.Registry.generateKeyboardEvent(keys["c"], None, pyatspi.KEY_PRESSRELEASE)
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
	#def selectAll

	def trackFocus(self):
		pyatspi.Registry.registerEventListener(self._emitFocusChanged, "object:state-changed:focused")
		pyatspi.Registry.start()
	
	def _emitFocusChanged(self,event):
		component=event.source
		print(event.detail1)
		print(parent)
		print(event.source)
		print(component, " got focus " if event.detail1 else " lost focus")
		pyatspi.Registry.stop()
#class a11Manager

