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
import llxaccessibility.libs.clipboardManager as clipboardManager
import llxaccessibility.libs.a11Manager as a11Manager
from PySide6.QtWidgets import QApplication

class client():
	def __init__(self):
		self.dbg=True
		if QApplication.instance()==None:
			app=QApplication(["tts"])
		self.profile=profileManager.manager()
		self.tts=ttsManager.manager()
		self.sddm=sddmManager.manager()
		self.kwin=kwinManager.manager()
		self.kconfig=kconfig.kconfig()
		self.imageProcessing=imageProcessing.imageProcessing()
		self.a11Manager=a11Manager.a11Manager()
		self.clipboard=clipboardManager.clipboardManager()
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
		kcm="kcmshell5"
		cmd=["plasmashell","-v"]
		proc=subprocess.check_output(cmd,encoding="utf8",universal_newlines=True)
		for l in proc.split("\n"):
			if l.strip().startswith("plasmashell "):
				ver=l.split(" ")[1].split(".")[0]
				kcm=kcm.replace("5",ver)
		cmd=[kcm,kcmModule]
		proc=self.launchCmd(cmd)
		return(proc)
	#def launchKcmModule

	def launchKcmModuleAsync(self,kcmModule):
		kcm="kcmshell5"
		cmd=["plasmashell","-v"]
		proc=subprocess.check_output(cmd,encoding="utf8",universal_newlines=True)
		for l in proc.split("\n"):
			if l.strip().startswith("plasmashell "):
				ver=l.strip().split(" ")[1].split(".")[0]
				kcm=kcm.replace("5",ver)
		cmd=[kcm,kcmModule]
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

	def setMonoAudio(self,state=True,enable=True):
		if state==True:
			self.tts.setMonoAudio(enable)
		else:
			self.tts.disableMonoAudio()
	#def setMonoAudio

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

	def trackFocus(self,callback,oneshot=False):
		self.a11Manager.trackFocus(callback,oneshot)
	#def trackFocus

	def getCurrentFocusCoords(self,):
		return(self.a11Manager.getCurrentFocusCoords())
	#def trackFocus

	def readScreen(self,*args,onlyClipboard=False,onlyScreen=False,**kwargs):
		txt=""
		tmpimg=kwargs.get("img","/tmp/out.png")
		lang=self.readKFile("kwinrc","Script-ocrwindow","Voice")
		clipboard=self.readKFile("kwinrc","Script-ocrwindow","Clipboard")
		spellcheck=self.readKFile("kwinrc","Script-ocrwindow","Spellchecker")
		scripts=self.kwin.getKWinScripts()
		script=scripts.get("ocrwindow",{})
		path=os.path.join("{}".format(os.path.dirname(script.get("path",""))),"contents","ui","config.ui")
		lang=self.kconfig.getTextFromValueKScript(path,"Voice",lang)
		langdict={"spanish":"es","valencian":"ca"}
		lang=langdict.get(lang.lower(),"en")
		if clipboard=="":
			clipboard=False
		item=self.clipboard.getClipboardContents()
		if isinstance(item,str):
			if "://" in item and item.count(" ")==0 and item.count("/")>1:
				protocol=item.split(":")[0]
				if protocol.startswith("http"):
					urllib.request.urlretrieve(item, tmpimg)
				elif protocol.startswith("file"):
					tmpimg="".join(item.split(":")[1:]).replace("//","/")
				else:
					txt=item
			else:
				txt=item
		if len(txt)==0:
			if spellcheck==False:
				lang=""
			(lang,txt)=self.getImageOcr(spellcheck=spellcheck,img=tmpimg,lang=lang)
			#self._debug("Detected IMAGE LANGUAGE {}".format(detectedLang[0]))
		else:
			lang=langid.classify(txt)[0]
			#self._debug("Detected CLIPBOARD LANGUAGE {}".format(detectedLang[0]))
		if len(txt)>0:
			self.tts.invokeReader(txt,lang=lang)
	#def readScreen

#class client

