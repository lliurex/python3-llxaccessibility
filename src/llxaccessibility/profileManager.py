#!/usr/bin/python3
import os
import tarfile
import tempfile
import shutil

class manager():
	def __init__(self):
		self.dbg=True
		self.prflDir=os.path.join(os.environ.get("HOME"),".local","share","accesswizard","profiles")
		if os.path.exists(self.prflDir)==False and os.environ.get("HOME","")!="":
			os.makedirs(self.prflDir)
	#def __init__

	def _debug(self,msg):
		if self.dbg:
			print("profileManager: {}".format(msg))
	#def _debug

	def _generateProfileDirs(self,pname):
		tmpDirs={}
		#Generate tmp folders
		tmpFolder=tempfile.mkdtemp()
		tmpDirs.update({"tmp":tmpFolder})
		#Plasma config goes to .config
		plasmaPath=os.path.join(tmpFolder,".config")
		os.makedirs(plasmaPath)
		tmpDirs.update({"plasma":plasmaPath})
		#accesswizard to .config/accesswizard and .local/share
		configPath=os.path.join(tmpFolder,".config/accesswizard")
		#onboard=os.path.join(os.path.dirname(appconfrc),"onboard.dconf")
		os.makedirs(configPath)
		tmpDirs.update({"config":configPath})
		localPath=os.path.join(tmpFolder,".local/share/accesswizard")
		os.makedirs(localPath)
		tmpDirs.update({"local":localPath})
		#autostart
		desktopStartPath=os.path.join(tmpFolder,".config/autostart")
		os.makedirs(desktopStartPath)
		#autostartPath=os.path.join(home,".config","autostart")
		tmpDirs.update({"autostart":desktopStartPath})
		#autoshutdown
		desktopShutdownPath=os.path.join(tmpFolder,".config/plasma-workspace/shutdown")
		os.makedirs(desktopShutdownPath)
		#autoshutdownPath=os.path.join(home,".config",".config/plasma-workspace/shutdown")
		tmpDirs.update({"autoshutdown":desktopShutdownPath})
		#mozilla
		mozillaPath=os.path.join(tmpFolder,".mozilla")
		os.makedirs(mozillaPath)
		tmpDirs.update({"mozilla":mozillaPath})
		#gtk
		gtkPath=os.path.join(tmpFolder,".config")
		if os.path.isdir(gtkPath)==False:
			os.makedirs(gtkPath)
		tmpDirs.update({"gtk":gtkPath})
		return(tmpDirs)
	#def _generateProfileDirs

	def _copyKFiles(self,plasmaPath):
		klist=["kcminputrc","konsolerc","kglobalshortcutsrc","khotkeys","kwinrc","kaccessrc"]
		for kfile in klist:
			kPath=os.path.join(os.environ['HOME'],".config",kfile)
			if os.path.isfile(kPath):
				shutil.copy(kPath,plasmaPath)
	#def _copyKFiles(self):

	def _copyAccessFiles(self,configPath):
		blacklist=["records","profiles"]
		print("CPath: {}".format(configPath))
		if "/.local/" in configPath:
			sourcePath=os.path.join(os.environ.get("HOME"),".local","share","accesswizard")
		else:
			sourcePath=os.path.join(os.environ.get("HOME"),".config","accesswizard")
		print("Accessing {}".format(sourcePath))
		if os.path.exists(sourcePath):
			for f in os.scandir(sourcePath):
				print("GET: {}".format(f.path))
				if os.path.isdir(f.path):
					if f.name not in blacklist:
						print("DIR: {} >> {}".format(f.path,configPath))
						shutil.copytree(f.path,os.path.join(configPath,f.name),dirs_exist_ok=True)
				else:
					shutil.copy(f.path,configPath)
	#def _copyAccessFiles

	def _copyStartShutdown(self,desktopstartPath,desktopshutdownPath):
		autoshutdownPath=os.path.join(os.environ.get("HOME"),".config",".config/plasma-workspace/shutdown")
		autostartPath=os.path.join(os.environ.get("HOME"),".config",".config/autostart")
		for auto in [autostartPath,autoshutdownPath]:
			if os.path.isdir(auto):
				for f in os.listdir(auto):
					if f.startswith("access"):
						autostart=os.path.join(auto,f)
						if auto==autostartPath:
							shutil.copy(autostart,desktopStartPath)
						else:
							shutil.copy(autostart,desktopShutdownPath)
	#def _copyStartShutdown

	def _getMozillaSettingsFiles(self):
		mozillaFiles=[]
		mozillaDir=os.path.join(os.environ.get('HOME',''),".mozilla/firefox")
		if os.path.isdir(mozillaDir)==True:
			for mozillaF in os.listdir(mozillaDir):
				self._debug("Reading MOZILLA {}".format(mozillaF))
				fPath=os.path.join(mozillaDir,mozillaF)
				if os.path.isdir(fPath):
					self._debug("Reading DIR {}".format(mozillaF))
					if "." in mozillaF:
						self._debug("Reading DIR {}".format(mozillaF))
						prefs=os.path.join(mozillaDir,mozillaF,"prefs.js")
						if os.path.isfile(prefs):
							mozillaFiles.append(prefs)
		return mozillaFiles
	#def _getMozillaSettingsFiles

	def _copyMozillaFiles(self,mozillaPath):
		mozillaFiles=self._getMozillaSettingsFiles()
		for mozillaFile in mozillaFiles:
			destdir=os.path.basename(os.path.dirname(mozillaFile))
			destdir=os.path.join(mozillaPath,destdir)
			os.makedirs(destdir)
			shutil.copy(mozillaFile,destdir)
	#def _copyMozillaFiles

	def _getGtkSettingsFiles(self,checkExists=False):
		gtkFiles=[]
		gtkDirs=[os.path.join("/home",os.environ.get('USER',''),".config/gtk-3.0"),os.path.join("/home",os.environ.get('USER',''),".config/gtk-4.0")]
		for gtkDir in gtkDirs:
			if checkExists==False:
				gtkFiles.append(os.path.join(gtkDir,"settings.ini"))
			elif os.path.isfile(os.path.join(gtkDir,"settings.ini"))==True:
				gtkFiles.append(os.path.join(gtkDir,"settings.ini"))
		return gtkFiles
	#def _getGtkFiles

	def _copyGtkFiles(self,gtkPath):
		gtkFiles=self._getGtkSettingsFiles(True)
		for gtkFile in gtkFiles:
			destdir=os.path.basename(os.path.dirname(gtkFile))
			destdir=os.path.join(gtkPath,destdir)
			os.makedirs(destdir)
			shutil.copy(gtkFile,destdir)
	#def _copyGtkFiles(self):

	def _copyTarProfile(self,orig,dest):
		if os.path.isdir(os.path.dirname(dest))==False:
			os.makedirs(os.path.dirname(dest))
		try:
			shutil.copy(orig,dest)
		except Exception as e:
			self._debug(e)
			self._debug("Permission denied for {}".format(dest))
			sw=False
	#def _copyTarProfile
	
	def saveProfile(self,pname="profile"):
		prflDir=os.path.join(os.environ.get("HOME"),".local","share","accesswizard","profiles",pname)
		profiles=[]
		if os.path.exists(os.path.dirname(prflDir))==False:
			os.makedirs(prflDir)
		if os.path.exists(prflDir)==True:
			shutil.rmtree(prflDir)
		os.makedirs(prflDir)
		self._debug("Saving profile {}".format(prflDir))
		prflDirs=self._generateProfileDirs(pname)
		self._copyKFiles(prflDirs["plasma"])
		self._copyAccessFiles(prflDirs["config"])
		self._copyAccessFiles(prflDirs["local"])
		self._copyStartShutdown(prflDirs["autostart"],prflDirs["autoshutdown"])
		self._copyMozillaFiles(prflDirs["mozilla"])
		self._copyGtkFiles(prflDirs["gtk"])
		(osHdl,tmpFile)=tempfile.mkstemp()
		oldCwd=os.getcwd()
		tmpFolder=prflDirs["tmp"]
		os.chdir(tmpFolder)
		with tarfile.open(tmpFile,"w") as tarFile:
			for f in os.listdir(tmpFolder):
				tarFile.add(os.path.basename(f))
		os.chdir(oldCwd)
		if prflDir.endswith(".tar")==False:
			prflDir+=".tar"
		self._debug("Copying {0}->{1}".format(tmpFile,prflDir))
		self._copyTarProfile(tmpFile,prflDir)
		os.remove(tmpFile)
		return(os.path.join(prflDir,os.path.basename(tmpFile)))
	#def saveProfile

	def _isValidTar(self,ppath):
		sw=False
		if os.path.isfile(ppath):
			sw=tarfile.is_tarfile(ppath)
		if sw==False:
			print("Error: {} is not a valid tar".format(ppath))
		return(sw)
	#def _isValidTar

	def _extractProfile(self,ppath,merge=False):
		sw=self._isValidTar(ppath)
		if sw==True:
			tarProfile=tarfile.open(ppath,'r')
			tmpFolder=tempfile.mkdtemp()
			tarProfile.extractall(path=tmpFolder)
			try:
				home=os.environ.get("HOME","")
				if len(home)>0:
					shutil.copytree(tmpFolder,home,dirs_exist_ok=True)
			except Exception as e:
				sw=False
				print("{} could not be restored".format(tmpFolder))
				print(e)
				print("----------")
		return(sw)
	#def _extractProfile

	def loadProfile(self,ppath):
		if os.path.exists(ppath)==True:
			#Backup current
			self.saveProfile("backup")
			#restore
			self._extractProfile(ppath)
	#def loadProfile

	def listProfiles(self):
		profiles=[]
		if os.path.exists(self.prflDir):
			for f in os.scandir(self.prflDir):
				if f.name.endswith(".tar"):
					profiles.append(f.name)
		return(profiles)
	#def listProfiles

	def getProfilesDir(self):
		return(self.prflDir)
	#def getProfilesDir

#class manager
