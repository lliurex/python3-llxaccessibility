#!/usr/bin/python3
import os
from orca import orca
import subprocess
from . import kconfig

class speaker():
	def __init__(self,*args,**kwargs):
		super().__init__()
		self.dbg=True
		self.txtFile=kwargs.get("txtFile")#.encode('iso8859-15',"replace")
		self.stretch=float(kwargs.get("stretch",1))
		self.voice=kwargs.get("voice","kal")
		self.currentDate=kwargs.get("date","240101")
		self.synth=kwargs.get("synth","")
		self.kconfig=kconfig.kconfig()
		self.orca=None
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("speaker: {}".format(msg))
	#def _debug

	def setParms(self,*args,**kwargs):
		self.stretch=float(kwargs.get("stretch",1))
		self.voice=kwargs.get("voice","kal")
		self.currentDate=kwargs.get("date","240101")
		self.synth=kwargs.get("synth","")
		self.txtFile=kwargs.get("txtFile","")
	#def setParms

	def run(self,txtFile=""):
		confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
		if os.path.exists(confDir)==False:
			os.makedirs(confDir)
		txt=txtFile
		if os.path.exists(self.txtFile):
			with open(self.txtFile,"r") as f:
				txt=f.read()
		self._runFestival(txt)
	#def run

	def _runFestival(self,txt):
		cfg=self.kconfig.getTTSConfig()
		if cfg["orca"]==True:
			if self.orca==None:
				self.orca=orca.speech
				self.orca.init()
			self._debug("ORCA")
			self.orca.speak(txt)
		else:
			confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
			stretch=cfg.get("stretch",1)
			rate=cfg.get("rate",1)
			speed=cfg.get("speed",1)
			stretch=stretch+((stretch-1)/100)
			voiceLanguage=self.kconfig.getTextFromValueKScript("ocrwindow","voice",cfg.get("voice",0))
			voice=self._getDefaultVoiceForLanguage(voiceLanguage)
			self._debug("Voice: {0}\nStretch: {1} Rate:{2} Speed:{3}".format(voice,stretch,rate,speed))
			p=subprocess.Popen(["festival","--pipe"],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			if voice.startswith("voice_")==False:
				voice="voice_{}".format(voice)
			p.stdin.write("({})\n".format(voice).encode("utf8"))
			p.stdin.write("(Parameter.set 'Duration_Stretch {})\n".format(stretch).encode("utf8"))
			p.stdin.write("(set! utt (Utterance Text {}))\n".format(txt).encode("utf8"))
			p.stdin.write("(utt.synth utt)\n".encode("utf8"))
			p.stdin.write("(utt.save.wave utt \"/tmp/.baseUtt.wav\" \'riff)\n".encode("utf8"))
			p.communicate()
			p.terminate()
			mp3Dir=os.path.join(confDir,"mp3")
			mp3File=os.path.join(mp3Dir,"{}.mp3".format(self.currentDate))
			p=subprocess.run(["lame","/tmp/.baseUtt.wav",mp3File],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			#os.unlink("/tmp/.baseUtt.wav")
#			msgBox=QMessageBox()
#			msgTxt=_("TTS finished. Listen?")
#			msgInformativeTxt=_("Image was processesed")
#			msgBox.setText(msgTxt)
#			msgBox.setInformativeText(msgInformativeTxt)
#			msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
#			msgBox.setDefaultButton(QMessageBox.Yes)
#			ret=msgBox.exec()
#			if ret==QMessageBox.Yes:
			if self.synth=="vlc":
				#self._debug("Playing {} with vlc".format(mp3))
				prc=subprocess.run(["vlc",mp3File])
			else:
				#self._debug("Playing {} with TTS Strech {}".format(mp3,self.stretch))
				prc=subprocess.run(["play",mp3File])
		return 
	#def run

	def _getDefaultVoiceForLanguage(self,lang):
		self._debug("Search voice for {}".format(lang))
		wrkdir=os.path.join("/","usr","share","festival","voices")
		lang=lang.lower()
		if lang=="valencian":
			lang="catalan"
		if os.path.exists(os.path.join(wrkdir,lang))==False:
			lang="english"
		defaultVoice=os.listdir(os.path.join(wrkdir,lang))[0]
		return(defaultVoice)

#class speaker
