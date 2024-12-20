#!/usr/bin/python
import subprocess
from . import kconfig

class manager():
	def __init__(self,parent=None):
		self.dbg=False
		self.kconfig=kconfig.kconfig()

	def getSDDMSound(self):
		state=False
		cmd=["/usr/bin/systemctl","is-enabled","pulse-sddm"]
		try:
			out=subprocess.check_output(cmd,universal_newlines=True,encoding="utf8")
			retval=True
		except Exception as e:
			out="disabled"
		if out.strip()=="enabled":
			state=True
		return(state)
	#def setSDDMSound

	def setSDDMSound(self,state=True):
		if state==True:
			action="enable"
			state=False
		cmd=["/usr/bin/systemctl",action,"pulse-sddm"]
		try:
			out=subprocess.check_output(cmd,universal_newlines=True,encoding="utf8")
		except Exception as e:
			out="disabled"
		if out.strip()=="enabled":
			state=True
		return(state)
	#def setSDDMSound

	def setSessionSound(self,state=True):
		action=""
		if state==True:
			action="Sound"
		self.kconfig.writeKFile("plasma_workspace.notifyrc","Event/startkde","Action",action)
		return(state)
	#def setSessionSound

	def getSessionSound(self):
		state=False
		if len(self.kconfig.readKFile("plasma_workspace.notifyrc","Event/startkde","Action"))>0:
			state=True
		return(state)
	#def getSessionSound

#class 
