import pyatspi
import time

keys={"CTRL":105,
	"a":38,
	"c":54
	}

class a11Manager():
	def __init__(self,*args,**kwargs):
		self.dbg=True
		self.desktop = pyatspi.Registry.getDesktop(0)
		self._debug("Desktop at {}".format(self.desktop))

	def _debug(self,msg):
		if self.dbg==True:
			print("a11Manager: {}".format(msg))

	def activeWindow(self):
		self._debug("Get active window")
		for app in self.desktop:
			for window in app:
				if window.getState().contains(pyatspi.STATE_ACTIVE):
					return app
	#def active_window

	def print_tree(level,root):
		print ('%s-> %s' % (' ' * level, root))
		for tree in root:
			print_tree(level+1, tree)
	#def print_tree

	def selectAll(self):
		time.sleep(1)
		app=self.activeWindow()
		print(app)
		if app!=None:
			chld=app.getChildAtIndex(0).getChildAtIndex(0)
			if chld==None:
				chld=app.getChildAtIndex(0)
			chld.queryComponent().grabFocus()
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
			pyatspi.Registry.generateKeyboardEvent(keys["a"], None, pyatspi.KEY_PRESSRELEASE)
			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
			time.sleep(0.1)
#			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_PRESS)
#			pyatspi.Registry.generateKeyboardEvent(keys["c"], None, pyatspi.KEY_PRESSRELEASE)
#			pyatspi.Registry.generateKeyboardEvent(keys["CTRL"], None, pyatspi.KEY_RELEASE)
	#def selectAll

