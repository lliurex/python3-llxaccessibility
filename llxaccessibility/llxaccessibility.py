#!/usr/bin/python3
import subprocess,os,sys,shutil
import multiprocessing
import urllib
import json
import py3langid as langid
import llxaccessibility.libs.profileManager as profileManager
import llxaccessibility.libs.ttsManager as ttsManager
import llxaccessibility.libs.imageProcessing as imageProcessing
import llxaccessibility.libs.sddmManager as sddmManager
import llxaccessibility.libs.kwinManager as kwinManager
import llxaccessibility.libs.kconfig as kconfig
from PySide2.QtWidgets import QApplication

class client():
	def __init__(self):
		self.dbg=True
		self.bus=None
		if QApplication.instance()==None:
			app=QApplication(["tts"])
		self.profile=profileManager.manager()
		self.tts=ttsManager.manager()
		self.sddm=sddmManager.manager()
		self.kwin=kwinManager.manager()
		self.kconfig=kconfig.kconfig()
		self.imageProcessing=imageProcessing.imageProcessing()
	#def __init__

	def _debug(self,msg):
		if self.dbg:
			print("libaccess: {}".format(msg))
	#def _debug

	def getDockEnabled(self):
		return(self.profile.getDockEnabled())
	#def getDockEnabled

	def setDockEnabled(self,state):
		return(self.profile.setDockEnabled(state))
	#def setDockEnabled
	
	def getGrubBeep(self):
		state=False
		fpath="/etc/default/grub"
		if os.path.exists(fpath):
			with open(fpath,"r") as f:
				for l in f.readlines():
					if l.replace(" ","").startswith("GRUB_INIT_TUNE"):
						state=True
						break
		return(state)
	#def getGrubBeep

	def writeKFile(self,*args,**kwargs):
		return(self.kconfig.writeKFile(*args,**kwargs))

	def readKFile(self,*args,**kwargs):
		return(self.kconfig.readKFile(*args,**kwargs))

	def getKWinEffects(self):
		return(self.kwin.getKWinEffects())

	def getKWinScripts(self):
		return(self.kwin.getKWinScripts())
	#def getKWinScripts(self):

	def getKWinPlugins(self,categories=["Accessibility"]):
		return(self.kwin.getKWinPlugins(categories))
	#def getKWinPlugins

	def getPluginEnabled(self,plugin):
		return(self.kwin.getPluginEnabled(plugin))
	#def getPluginEnabled

	def togglePlugin(self,plugin):
		return(self.kwin.togglePlugin(plugin))
	#def togglePlugin

	def applyKWinChanges(self):
		return(self.kwin.applyKWinChanges())
	#def applyKWinChanges

	def getClipboardText(self):
		return(self.kwin.getClipboardText())

	def getImageOcr(self,*args,**kwargs):
		return(self.imageProcessing.getImageOCR(*args,**kwargs))

	def _mpLaunchCmd(self,cmd):
		proc=None
		try:
			proc=subprocess.run(cmd)
		except Exception as e:
			print (e)
		return(proc)
	#def _mpLaunchKcm

	def launchKcmModule(self,kcmModule):
		cmd=["kcmshell5",kcmModule]
		proc=self.launchCmd(cmd)
		return(proc)
	#def launchKcmModule

	def launchKcmModuleAsync(self,kcmModule):
		cmd=["kcmshell5",kcmModule]
		proc=self.launchCmdAsync(cmd)
		return(proc)
	#def launchKcmModule

	def launchCmdAsync(self,cmd):
		proc=multiprocessing.Process(target=self._mpLaunchCmd,args=(cmd,))
		proc.daemon=True
		proc.start()
		return(proc)
	#def launchCmdAsync

	def launchCmd(self,cmd):
		proc=self._mpLaunchCmd(cmd)
		return(proc)
	#def launchCmd
	
	def saveProfile(self,pname="profile"):
		self.profile.saveProfile(pname)
	#def saveProfile

	def loadProfile(self,ppath="profile"):
		self.profile.loadProfile(ppath)
	#def take_snapshot

	def listProfiles(self):
		return(self.profile.listProfiles())
	#def listProfiles
		
	def getProfilesDir(self):
		return(self.profile.getProfilesDir())
	#def getProfilesDir

	def getTtsFiles(self):
		return(self.tts.getTtsFiles())
	#def getTtsFiles

	def getFestivalVoices(self):
		return(self.tts.getFestivalVoices())
	#def getFestivalVoices

	def getSessionSound(self):
		return(self.sddm.getSessionSound())
	#def getSessionSound

	def setSessionSound(self,state=True):
		return(self.sddm.setSessionSound(state))
	#def setSessionSound

	def getSDDMSound(self):
		return(self.sddm.getSDDMSound())
	#def setSDDMSound

	def setSDDMSound(self,state=True):
		return(self.sddm.setSDDMSound(state))
	#def setSDDMSound

	def getOrcaSDDM(self):
		sw=os.path.exists("/usr/share/accesswizard/tools/timeout")
		return sw
	#def getOrcaSDDM

	def setOrcaSDDM(self,timeout=0):
		if timeout>0:
			with open("/usr/share/accesswizard/tools/timeout","w") as f:
				f.write("CONT={}".format(timeout))
		else:
			if self.getOrcaSDDM():
				os.unlink("/usr/share/accesswizard/tools/timeout")
	#def setOrcaSDDM

	def readScreen(self,*args,onlyClipboard=False,onlyScreen=False):
		txt=""
		lang=self.readKFile("kwinrc","Script-ocrwindow","Voice")
		clipboard=self.readKFile("kwinrc","Script-ocrwindow","Clipboard")
		spellcheck=self.readKFile("kwinrc","Script-ocrwindow","Spellchecker")
		scripts=self.kwin.getKWinScripts()
		script=scripts.get("ocrwindow",{})
		path=os.path.join("{}".format(os.path.dirname(script.get("path",""))),"contents","ui","config.ui")
		lang=self.kconfig.getTextFromValueKScript(path,"Voice",lang)
		langdict={"spanish":"es","valencian":"ca"}
		lang=langdict.get(lang.lower(),"en")
		if clipboard==True:
			txt=self.getClipboardText()
			detectedLang=langid.classify(txt)
			self._debug("Detected CLIPBOARD LANGUAGE {}".format(detectedLang[0]))
			if detectedLang[0]!=lang:
				lang=detectedLang[0]
		if len(txt)==0:
			if spellcheck==False:
				lang=""
			(lang,txt)=self.getImageOcr(spellcheck=spellcheck,onlyScreen=not(clipboard),lang=lang)
		if len(txt)>0:
			if txt.startswith("http") and "://" in txt and txt.count(" ")==0 and txt.count("/")>2 and (".jpg" in txt or ".png" in txt):
				urllib.request.urlretrieve(txt, "/tmp/out.png")
				(lang,txt)=self.getImageOcr(spellcheck=spellcheck,onlyScreen=not(clipboard),lang=lang,img="/tmp/out.png")
			self.tts.invokeReader(txt,lang=lang)
	#def readScreen

#class client

