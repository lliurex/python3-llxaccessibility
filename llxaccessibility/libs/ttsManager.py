#!/usr/bin/python3
### This library implements atspi communications
import os,shutil
from orca import orca
import subprocess
from datetime import datetime
from collections import OrderedDict
from .speaker import speaker
from .kconfig import kconfig

class manager():
	def __init__(self):
		self.dbg=True
		self.libfestival="/usr/share/accesshelper/stacks/libfestival.py"
		self.confDir=os.path.join(os.environ.get('HOME','/tmp'),".local/share/accesswizard")
		self.txtDir=os.path.join(self.confDir,"records/txt")
		self.mp3Dir=os.path.join(self.confDir,"records/mp3")
		if os.path.isdir(self.txtDir)==False:
			os.makedirs(self.txtDir)
		if os.path.isdir(self.mp3Dir)==False:
			os.makedirs(self.mp3Dir)
		self.pitch=50
		self.stretch=0
		self.setRate(1)
		self.voice="JuntaDeAndalucia_es_pa_diphone"
		self.synth="vlc"
		self.speaker=speaker()
		self.kconfig=kconfig()
	#def __init__

	def _debug(self,msg):
		if self.dbg:
			print("speech: {}".format(msg))
	#def _debug

	def setRate(self,speed):
		#3x=0.40 0x=1.40 1x=0.90
		#steps are 0.25. Between 3 and 0 there are 12 steps
		#speed/0.25=Steps from 0x. Each step=8.3
		speed=abs(float(speed)-3)
		steps=float(speed)/0.25
		self.stretch=(steps*0.083)+0.40
		#return speed
	#def _setRate

	def setVoice(self,voice):
		self.voice=voice
		if self.voice.startswith("voice_")==False:
			self.voice="voice_{}".format(self.voice)
	#def setVoice

	def setPlayer(self,player):
		if player=="vlc":
			self.synth="vlc"
		else:
			self.synth="orca"
	#def setVoice

	def sayFile(self,txtFile,currentDate,locale=""):
		if isinstance(currentDate,str)==False:
			currentDate=currentDate.strftime("%Y%m%d_%H%M%S")
		self._debug("Date type {}".format(type(currentDate)))
		self.speaker.setParms(txtFile=txtFile,stretch=self.stretch,voice=self.voice,date=currentDate,synth=self.synth)
		self.speaker.run(locale=locale)
	#def sayFile

	def invokeReader(self,txt,lang=""):
		currentDate=datetime.now()
		fileName="{}.txt".format(currentDate.strftime("%Y%m%d_%H%M%S"))
		txtFile=os.path.join(self.txtDir,fileName)
		txt=txt.replace("\"","\'")
		with open(txtFile,"w") as f:
			f.write("\"{}\"".format(txt))
		self._debug("Generating with Strech {}".format(self.stretch))
		prc=self.sayFile(txtFile,currentDate,locale=lang)
		return(prc)
	#def _invokeReader

	def getFestivalVoices(self):
		voices={}
		voicesFolder="/usr/share/festival/voices/"
		if os.path.isdir(voicesFolder):
			for lang in os.listdir(voicesFolder):
				voices[lang]=os.listdir(os.path.join(voicesFolder,lang))
		return(voices)
	#def getFestivalVoices

	def getTtsFiles(self):
		allDict={}
		mp3Dict={}
		txtDict={}
		if os.path.isdir(self.mp3Dir)==True:
			for f in os.scandir(self.mp3Dir):
				if f.name.endswith(".mp3") and "_" in f.name:
					mp3Dict[f.name.replace(".mp3","")]=f.name
		if os.path.isdir(self.txtDir)==True:
			for f in os.scandir(self.txtDir):
				if f.name.endswith(".txt") and "_" in f.name:
					txtDict[f.name.replace(".txt","")]=f.name
		for key,item in mp3Dict.items():
			allDict[key]={"mp3":item}
		for key,item in txtDict.items():
			if allDict.get(key):
				allDict[key].update({"txt":item})
			else:
				allDict[key]={"txt":item}
		ordDict=OrderedDict(sorted(allDict.items(),reverse=True))
		return(ordDict)
	#def getTtsFiles
	
	def setMonoSound(self):
		env=os.environ
		env.update({"LANG":"C"})
		out=subprocess.check_output(["pactl","info"],env=env,encoding="utf8")
		for l in out.split("\n"):
			if l.strip().startswith("Default Source:"):
				defaultSource=l.split(" ")[-1]
		paDir=os.path.join(os.environ["HOME"],".config","pipewire","pipware.conf.d")
		fContent='context.modules = [\n\
{   name = libpipewire-module-combine-stream\n\
        args = {\n\
            combine.mode = sink\n\
            node.name = "Mono" \n\
            node.description = "Mono" \n\
            combine.latency-compensate = false\n\
            combine.props = {\n\
            audio.position = [ MONO ]\n\
            }\n\
            stream.props = {\n\
                stream.dont-remix = true\n\
            }\n\
            stream.rules = [\n\
            {   matches = [\n\
                    {   media.class = "Audio/Sink"\n\
                        node.name = NODE_NAME\n\
                    } ]\n\
                    actions = { create-stream = {\n\
                            audio.position = [ FL FR ]\n\
                            combine.audio.position = [ MONO ]\n\
                    } } }\n\
            ]\n\
        }\n\
    }\n\
]'
		fContent=fContent.replace("NODE_NAME",defaultSource)
		if not os.path.exists(paDir):
			os.makedirs(paDir)
		with open(os.path.join(paDir,"mono.conf"),"w") as f:
			f.write(fContent)
	#def setMonoSound

