#!/usr/bin/python
import subprocess
import json
import os
class kconfig():
	def __init__(self,parent=None):
		self.dbg=False

	def readKFile(self,kfile,group,key):
		cmd=["kreadconfig5","--file",kfile,"--group",group,"--key",key]
		out=subprocess.check_output(cmd,universal_newlines=True,encoding="utf8").strip()
		return(out)
	#def readKFile

	def writeKFile(self,kfile,group,key,data):
		if isinstance(data,str)==False:
			data=str(data).lower()
		cmd=["kwriteconfig5","--file",kfile,"--group",group,"--key",key,data]
		out=subprocess.check_output(cmd)
		self._debug(out)
		return(out)
	#def writeKFile

	def getTextFromValueKScript(self,path,group,value):
		items=[]
		text=""
		if group.startswith("kcfg_")==False:
			group="kcfg_{}".format(group.capitalize())
		if os.path.exists(path):
			item=False
			with open(path,"r") as f:
				for fline in f.readlines():
					line=fline.strip()
					if "ComboBox" in line and group in line:
						item=True
						continue
					if item==True:
						if "</widget>" in line:
							item=False	
							break
						if "<string>" in line.lower():
							items.append(line.removeprefix("<string>").removesuffix("</string>"))
		if len(items)>=int(value):
			text=items[int(value)]
		return text
	#def getXmlTextFromValueScriptXml

	def readMetadata(self,path):
		metapath=""
		data={}
		exts=["json","desktop"]
		if os.path.isdir(path):
			for ext in exts:
				if os.path.isfile(os.path.join(path,"metadata.{}".format(ext))):
					metapath=os.path.join(path,"metadata.{}".format(ext))
					break
		else:
			for ext in exts:
				if os.path.basename(path)=="metadata.{}".format(ext) and os.path.isfile(path):
					metapath=path
					break
		if metapath.endswith(".json"):
			data=self._readMetadataJson(metapath)
		elif metapath.endswith(".desktop"):
			data=self._readMetadataDesktop(metapath)
		data.update({"path":metapath})
		return(data)
	#def readMetadata

	def _readMetadataDesktop(self,path):
		data={}
		with open(path,"r") as f:
			fdata=f.readlines()
		if len(fdata)>0:
			data.update({"KPackageStructure":"KWin/Effect"})
			data.update({"KPlugin":{}})
			for line in fdata:
				fields=line.split("=")
				if fields[0]=="Name":
					data["KPlugin"].update({fields[0]:fields[1].strip()})
				elif fields[0]=="Comment":
					data["KPlugin"].update({"Description":fields[1].strip()})
				elif fields[0]=="Icon":
					data["KPlugin"].update({fields[0]:fields[1].strip()})
				elif fields[0]=="X-KDE-ServiceTypes":
					data["KPackageStructure"]=fields[1].strip()
				elif fields[0]=="X-KDE-PluginInfo-Name":
					data["KPlugin"].update({"Id":fields[1].strip()})
				elif fields[0]=="X-KDE-PluginInfo-Category":
					data["KPlugin"].update({"Category":fields[1].strip()})
		return(data)
	#def _readMetadataDesktop

	def _readMetadataJson(self,path):
		data="{}"
		with open(path,"r") as f:
			data=f.read()
		data=json.loads(data)
		return(data)
	#def _readMetadataJson

	def getTTSConfig(self):
		#REM SYNTH IS NOT FALSE, it's one from orca,synth,vlc
		kconfig={}
		for key in ["pitch","stretch","voice","rate","orca","vlc","synth"]:
			cfg=self.readKFile("kwinrc","Script-ocrwindow",key.capitalize())
			if isinstance(cfg,str):
				if cfg=="true":
					cfg=True
				elif cfg=="false":
					cfg=False
				elif cfg.isnumeric()==True:
					cfg=int(cfg)
				elif cfg.isalpha()==False: #decimal
					cfg=float(a)
			kconfig.update({key:cfg})
		return(kconfig)
	#def getTTSConfig
