#!/usr/bin/python3
import os
from orca import orca
import subprocess
import multiprocessing
import tempfile
import shutil
import time
import speechd
try:
	from . import kconfig
except:
	import kconfig

class speaker():
	def __init__(self,*args,**kwargs):
		super().__init__()
		self.dbg=True
		self.txtFile=kwargs.get("txtFile")#.encode('iso8859-15',"replace")
		self.playing=False
		self.mp=None
		self.tmpFile=""
		self.voice=kwargs.get("voice","kal")
		self.currentDate=kwargs.get("date","240101")
		self.synth=kwargs.get("synth","")
		self.kconfig=kconfig.kconfig()
		self.spd=speechd.Speaker("accesshelper")
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

	def run(self,txt=""):
		confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
		if os.path.exists(confDir)==False:
			os.makedirs(confDir)
		if len(txt)==0:
			if os.path.exists(self.txtFile):
				with open(self.txtFile,"r") as f:
					txt=f.read()
		self._runSpd(txt)

	def _runSpd(self,txt):
		cfg=self.kconfig.getTTSConfig()
		orcaConfig=cfg.get("orca",{}).get("profiles",{}).get("default",{}).get("voices",{}).get("default",{})
		self.tmpFile=tempfile.mktemp(suffix=".mp3")
		stretch=int(cfg.get("stretch",1))
		pitch=int(orcaConfig.get("average-pitch",1))
		rate=int(orcaConfig.get("rate",cfg.get("rate",1)))
		#rate over 80. Stretch deprecated 
		stretch=int((stretch*100)-(rate*80/100)/100)
		#spd=speechd.Speaker("accesshelper")
		voiceLanguage=self.kconfig.getTextFromValueKScript("ocrwindow","voice",cfg.get("voice",0))
		(voiceLocale,voice)=self._getSpdVoiceForLanguage(voiceLanguage)
		voices=orcaConfig.get("family",{})
		voiceLocale=voices.get("lang",voiceLocale)
		voice=voices.get("name",voice)
		if self.spd!=None:
			self.spd==None
		self.spd=speechd.Speaker("accesshelper")
		self.spd.set_language(voiceLocale)
		self.spd.set_synthesis_voice(voice)
		self.spd.set_rate(rate)
		self.spd.set_pitch(pitch)
		self._debug("Voice: {} VoiceLocale: {} Rate: {} Pitch: {}".format(voice,voiceLocale,rate,pitch))
		mp=self.recordPulseStart()
		self.spd.speak(txt,self.recordPulseEnd)
	#def _runSpd

	def _getSpdVoiceForLanguage(self,lang):
		voice="female1"
		voiceLocale="en"
		if lang.lower()=="valencian":
			lang="catalan"
			voiceLocale="ca"
		elif lang.lower()=="spanish":
			voiceLocale="es"
		for spdlang in self.spd.list_synthesis_voices():
			if spdlang[0].strip().lower().startswith(lang.lower()) and "male" in spdlang[-1].lower():
				voiceLocale=spdlang[1]
				voice=spdlang[-1]
				break
		return(voiceLocale,voice)
	#def _getSpdVoiceForLanguage

	def recordPulseStart(self):
		self._debug("START Pulse recording")
		self.mp=multiprocessing.Process(target=self._capturePulseOutput,args=(self.tmpFile,),daemon=False)
		self.mp.start()
		#self._capturePulseOutput(outF)
	#def recordPulseStart

	def recordPulseEnd(self,*args):
		if args[0]=="begin":
			return
		time.sleep(1)
		confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
		mp3Dir=os.path.join(confDir,"mp3")
		mp3File=os.path.join(mp3Dir,"{}.mp3".format(self.currentDate))
		self.mp.kill()
		cmd=["killall","ffmpeg"]
		subprocess.run(cmd)
		shutil.move(self.tmpFile,mp3File)
		self._debug("PA: {}".format(mp3File))
	#def recordPulseEnd

	def _runFestival(self,txt):
		cfg=self.kconfig.getTTSConfig()
		confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
		stretch=float(cfg.get("stretch",1))
		rate=round(float(cfg.get("rate",0)),3)
		#rate over 90
		rate=(rate*80)/100
		stretch=round(stretch-(rate/100),3)
		voiceLanguage=self.kconfig.getTextFromValueKScript("ocrwindow","voice",cfg.get("voice",0))
		voice=self._getFestivalDefaultVoiceForLanguage(voiceLanguage)
		strech=15
		self._debug("Voice: {0}\nStretch: {1} Rate:{2}".format(voice,stretch,rate))

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
#		msgBox=QMessageBox()
#		msgTxt=_("TTS finished. Listen?")
#		msgInformativeTxt=_("Image was processesed")
#		msgBox.setText(msgTxt)
#		msgBox.setInformativeText(msgInformativeTxt)
#		msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
#		msgBox.setDefaultButton(QMessageBox.Yes)
#		ret=msgBox.exec()
#		if ret==QMessageBox.Yes:
		if self.synth=="vlc":
			#self._debug("Playing {} with vlc".format(mp3))
			prc=subprocess.run(["vlc",mp3File])
		else:
			#self._debug("Playing {} with TTS Strech {}".format(mp3,self.stretch))
			prc=subprocess.run(["play",mp3File])
		return 
	#def _runFestival

	def _getFestivalDefaultVoiceForLanguage(self,lang):
		self._debug("Search voice for {}".format(lang))
		wrkdir=os.path.join("/","usr","share","festival","voices")
		lang=lang.lower()
		if lang=="valencian":
			lang="catalan"
		if os.path.exists(os.path.join(wrkdir,lang))==False:
			lang="english"
		defaultVoice=os.listdir(os.path.join(wrkdir,lang))[0]
		return(defaultVoice)
	#def _getFestivalDefaultVoiceForLanguage

	def _capturePulseOutput(self,outF):
		try:
			confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard/records")
			defOutput=0
			cmd=["pacmd","list-sinks"]
			proc=subprocess.run(cmd,encoding="utf8",stderr=subprocess.PIPE,stdout=subprocess.PIPE)
			read=False
			self._debug("Reading sinks")
			for lproc in proc.stdout.split("\n"):
				if lproc.strip().startswith("* index"):
					read=True
					continue
				if read==True:
					if lproc.strip().startswith("name:"):
						defOutput=lproc.strip().split(" ")[-1].replace("<","").replace(">","")
						read=False
						break
					self._debug("Default output: {}".format(defOutput))
			cmd=["ffmpeg","-f","pulse","-ac","2","-i","{}.monitor".format(defOutput),outF]
			self._debug("RUN {}".format(cmd))
			subprocess.run(cmd)
		except Exception as e:
			self._debug("** Capture error: {}".format(e))
		return(defOutput)
	#def _capturePulseAudio
#class speaker
