#!/usr/bin/python3
import tesserocr
import py3langid as langid
from spellchecker import SpellChecker
import hunspell
import locale
import subprocess
import string
import os
import cv2
import imutils
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from PySide6.QtGui import QClipboard,QPixmap
try:
	from . import kconfig
except:
	import kconfig
try:
	from . import clipboardManager
except:
	import clipboardManager

TMPDIR="/tmp/.cache/accessibility/{}".format(os.environ.get("USER","tmp"))

class filters():
	def __init__(self,*args,**kwargs):
		self.dbg=True

	def _debug(self,msg):
		if self.dbg==True:
			print("imageFilter: {}".format(msg))
	#def _debug

	def analyzeImage(self,image,light=170,mid=100):
		dominantColor="dark"
		pixels=24
		pilImage=Image.fromarray(image)
		pilImage=pilImage.convert("RGBA")
		pilImage=pilImage.resize((pixels, pixels), resample=0)
		lightPoints={"light":0,"mid":0,"dark":0}
		for x in range(0,pixels):
			for y in range(0,pixels):
				colorAt0=pilImage.getpixel((x, y))
				#self._debug("Color detected: {}".format(colorAt0))
				if colorAt0[0]>light:
					lightPoints["light"]+=1
				elif colorAt0[0]>=mid:
					lightPoints["mid"]+=1
				else:
					lightPoints["dark"]+=1
		return(lightPoints)
	#def _analyzeImage

	def sum(self,imageBase,imageOverlay):
		image=imageBase.copy()
		x_offset=y_offset=0
		image[y_offset:y_offset+imageOverlay.shape[0], x_offset:x_offset+imageOverlay.shape[1]] = imageOverlay
		return(image)
	#def sum

	def resize(self,image,scale=3):
		return(cv2.resize(image, None,fx=scale,fy=scale))
	#def resize

	def opening(self,image,ratio=5):
		kernel = np.ones((ratio,ratio),np.uint8)
		return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
	#def opening

	def close(self,imageBase,ratio=5):
		image=imageBase.copy()
		kernel = np.ones((ratio,ratio),np.uint8)
		return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
	#def close

	def binaryThresholding(self,imageBase,low=160,high=255):
		image=imageBase.copy()
		return cv2.threshold(image, low, high, cv2.THRESH_BINARY)[1]
	#def binaryThresholding

	def thresholding(self,imageBase,low=160,high=255):
		image=imageBase.copy()
		#return(cv2.threshold(image, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1])
		return cv2.threshold(image, low, high, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
	#def thresholding

	def distance(self,imageBase):
		image=imageBase.copy()
		image=cv2.distanceTransform(image,cv2.DIST_L2,5)
		image=cv2.normalize(image, image, 0, 1.0, cv2.NORM_MINMAX)
		image=(image * 255).astype("uint8")
		return(image)
	#def distance
		 
	def morph(self,imageBase,ratio=5):
		image=imageBase.copy()
		kernel = np.ones((ratio,ratio),np.uint8)
		openingKernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ratio, ratio))
		image=cv2.dilate(image,kernel)
		image=cv2.morphologyEx(image, cv2.MORPH_OPEN,openingKernel)
		image=cv2.morphologyEx(image, cv2.MORPH_CLOSE,openingKernel)
		image = cv2.dilate(image,openingKernel,iterations = 1)
		return(image)
	#def morph

	def _grabCharsFromContours(self,image,minWidth=55,minHeight=120):
		# find contours in the opening image, then initialize the list of
		# contours which belong to actual characters that we will be OCR'ing
		cnts=cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_TC89_L1)
		cnts = imutils.grab_contours(cnts)
		chars = []
		oldchars = []
		# loop over the contours
		while  minWidth>=1:
			self._debug("Trying with {}".format(minWidth))
			chars=[]
			for c in cnts:
			# compute the bounding box of the contour
				(x, y, w, h) = cv2.boundingRect(c)
				# check if contour is at least 35px wide and 100px tall, and if
				# so, consider the contour a digit
				if w >= minWidth and h >= minHeight:
					chars.append(c)
			minWidth=minWidth/4
			minHeight=minWidth
			if chars<=oldchars and len(chars)>0:
				chars=oldchars
				break
			oldChars=chars

			self._debug("Computed: {}".format(len(chars)))
		return(chars)
	#def _grabCharsFromContours

	def _grabMaskForChars(self,image,imageBase,chars):
		try:
			chars = np.vstack([chars[i] for i in range(0, len(chars))])
		except:
			chars=[]
		mask = np.zeros(imageBase.shape[:2], dtype="uint8")
		if len(chars):
			hull = cv2.convexHull(chars)
			cv2.drawContours(mask, [hull], -1, 255, -1)
		mask = cv2.dilate(mask, None, iterations=2)
		return(mask)
	#def _grabMaskForChars

	def getContours(self,image,imageBase,minWidth=55,minHeight=120):
		chars=self._grabCharsFromContours(image,minWidth,minHeight)
		mask=self._grabMaskForChars(image,imageBase,chars)
		return cv2.bitwise_xor(image, imageBase, mask=mask)
	#def getContours

	def medianBlur(self,imageBase,kernel=2,blur=4,iterations=1):
		image=imageBase.copy()
		kernel = np.ones((kernel,kernel),np.uint8)
		dilation = cv2.dilate(image,kernel,iterations =iterations)
		image = cv2.medianBlur(image,blur)
		return(image)
	#def medianBlur

	def blur(self,imageBase):
		image=imageBase.copy()
		kernel = np.ones((5,5),np.uint8)
		dilation = cv2.dilate(image,kernel,iterations =5)
		blur =cv2.GaussianBlur(dilation,(3,3),0)
		image= cv2.erode(blur,kernel,iterations =5)
		image=cv2.Canny(image,100,200)
		return(image)
	#def blur(self,image):

	def erode(self,image,ratio=5):
		kernel = np.ones((ratio,ratio),np.uint8)
		image= cv2.erode(image,kernel,iterations =2)
		return(image)
	#def erode
	
	def cvGrayscale(self,imageBase):
		image=imageBase.copy()
		return(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
	#def cvGrayscale

	def cvCanny(self,imageBase,low=100,high=200):
		image=imageBase.copy()
		return cv2.Canny(image, low, high)
	#def cvCanny

	def smooth(self,imageBase):
		image=imageBase.copy()
		return cv2.bilateralFilter(image,15,50,50)
	#def smooth

	def gaussianAdaptative(self,imageBase,ratio=5):
		image=imageBase.copy()
		blur=cv2.GaussianBlur(image,(ratio,ratio),0)
		ret3,image = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		return(imageBase)
	#def gaussianAdaptative

	def gaussian(self,imageBase):
		image=imageBase.copy()
		blur = cv2.GaussianBlur(
			src=image,
			ksize=(3, 3),
			sigmaX=0,
			sigmaY=0,
		)
		# find normalized_histogram, and its cumulative distribution function
		hist = cv2.calcHist([blur],[0],None,[256],[0,256])
		hist_norm = hist.ravel()/hist.max()
		Q = hist_norm.cumsum()
		bins = np.arange(256)
		fn_min = np.inf
		thresh = -1
		for i in range(1,256):
			p1,p2 = np.hsplit(hist_norm,[i]) # probabilities
			q1,q2 = Q[i],Q[255]-Q[i] # cum sum of classes
			b1,b2 = np.hsplit(bins,[i]) # weights
			# finding means and variances
			m1,m2 = np.sum(p1*b1)/q1, np.sum(p2*b2)/q2
			v1,v2 = np.sum(((b1-m1)**2)*p1)/q1,np.sum(((b2-m2)**2)*p2)/q2
			# calculates the minimization function
			fn = v1*q1 + v2*q2
			if fn < fn_min:
				fn_min = fn
				thresh = i
		# find otsu's threshold value with OpenCV function
		ret, otsu = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		return(otsu)
	#def gaussian

	def cvDeskew(self,image):
		coords = np.column_stack(np.where(image > 0))
		angle = cv2.minAreaRect(coords)[-1]
		if angle < -45:
			angle = -(90 + angle)
		else:
			angle = -angle
		(h, w) = image.shape[:2]
		center = (w // 2, h // 2)
		M = cv2.getRotationMatrix2D(center, angle, 1.0)
		rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
		return rotated
	#def cvDeskew

	def thresholdingMask(self,image,ratio):
		low=0
		high=low+ratio
		imageTh=image
		imageTh=self.binaryThresholding(image,low,high)
		colorPoints=self.analyzeImage(imageTh,high,low)
		self._debug("COLOR POINTS: {}".format(colorPoints))
		while colorPoints.get("dark",0)<=ratio:
			low+=ratio
			high=low+ratio
			if low>=255:
				break
			imageTh=self.binaryThresholding(image,low,high)
			colorPoints=self.analyzeImage(imageTh,high,low)
			self._debug("COLOR POINTS ({0} {1}): {2}".format(low,high,colorPoints))
		imageTh=self.binaryThresholding(imageTh,low-ratio,255)
		return(imageTh)
#class filters

class imageProcessing():
	def __init__(self,parent=None):
		self.dbg=True
		self.filter=filters()
		self.clipboard=clipboardManager.clipboardManager()
		self.kconfig=kconfig.kconfig()
	#def __init__(self,parent=None):

	def _debug(self,msg):
		if self.dbg==True:
			print("imageProcessing: {}".format(msg))
	#def _debug
	
	def getImageOCR(self,spellcheck=True,onlyClipboard=False,onlyScreen=False,lang="en",img=""):
		txt=""
		if img=="" or os.path.exists(img)==False:
			img=self._getImgForOCR() #onlyClipboard,onlyScreen)
		imgPIL=None
		if os.path.isfile(img):
			img=self._processImg(img)
			try:
				imgPIL = Image.open(img)
				self._debug("Opened IMG. Waiting OCR")
			except Exception as e:
				print(e)
		if imgPIL:
			lang,txt=self._readImg(imgPIL,lang=lang,spellcheck=spellcheck)
		return(lang,txt)
	#def getImageOCR

	def _readImgFromClipboard(self,mode):
		img=self.clipboard.getClipboardContents()
		if isinstance(img,str):
			img=QPixmap()
		return(img)
	#def _readImgFromClipboard

	def _getImgForOCR(self,onlyClipboard=False,onlyScreen=False):
		cfg=self.kconfig.getTTSConfig()
		outImg=os.path.join(TMPDIR,"out.png")
		if os.path.exists(os.path.dirname(outImg))==False:
			os.makedirs(os.path.dirname(outImg))
		for f in os.scandir(os.path.dirname(outImg)):
			os.unlink(f.path)
		img=self._readImgFromClipboard(QClipboard.Clipboard)
		if onlyScreen==True:
			img=self._readImgFromClipboard(QClipboard.Selection)
		if img.isNull()==False:
			self.clipboard.popContentsAsync()
			self._debug("Getting clipboard IMG")
			img.save(outImg, "PNG")
		elif onlyScreen==True:
			self._debug("Taking Screenshot")
			if cfg.get("Screenshot",False)==False:
				subprocess.run(["spectacle","-a","-e","-b","-c","-o",outImg])
			else:
				subprocess.run(["spectacle","-r","-e","-b","-c","-o",outImg])
		return(outImg)
	#def _getImgForOCR
	
	def _saveDebugImg(self,image,text=""):
		if self.dbg==True:
			dbgImage=image
			cont=10
			if os.path.exists(TMPDIR)==False:
				os.makedirs(TMPDIR)
				os.chmod(TMPDIR,0o777)
			while True:
				if os.path.exists(os.path.join(TMPDIR,"out{}.png".format(cont)))==False:
					break
				cont+=10
			if len(text)>0:
				position = (10,50)
				cv2.putText(
					dbgImage, #numpy array on which text is written
					text, #text
					position, #position at which writing has to start
					cv2.FONT_HERSHEY_SIMPLEX, #font family
					1, #font size
					(209, 80, 0, 255), #font color
			3) #font stroke

			cv2.imwrite("{0}/out{1}.png".format(TMPDIR,cont),dbgImage)
	#def _saveDebugImg(self,image):

	def _processImg(self,img):
		cfg=self.kconfig.getTTSConfig()
		imgFilter=self.kconfig.getTextFromValueKScript("ocrwindow","filter",cfg.get("filter",0))
		self._debug("Postprocessing {} with {} filter".format(img,imgFilter))
		outImg="{}".format(img)
		image=cv2.imread(img,flags=cv2.IMREAD_COLOR)
		image=self.filter.cvGrayscale(image)
		image=self.filter.resize(image)
		self._saveDebugImg(image)
	#	colorPoints=self.filter.analyzeImage(image)
	#	if colorPoints.get("light",0)<(colorPoints.get("dark",0)+colorPoints.get("mid",0)):
	#		self._debug("Dark image detected")
	#		image=self._processDarkBkgImg(image)
	#	else:
	#		self._debug("Light image detected")
	#		image=self._processAltLightBkgImg(image)
		image=self._processDarkBkgImg(image)
		#If foreground=dark then test2 or test3 are way better
			#imageTh=self.filter.thresholding(image)
			#imageGaussian=self.filter.gaussianAdaptative(imageTh)
			#imageSmooth=self.filter.smooth(imageGaussian)
			#self._saveDebugImg(imageSmooth,"smooth")
			#image=self._processLightBkgImg(imageSmooth)
		self._debug("Saving processed img as {}".format(outImg))
		cv2.imwrite(outImg,image)
		return(outImg)
	#def _processImg

	def _processDarkBkgImg(self,image):
		imageBase=image
		imageBlur=self.filter.gaussian(image)
		thRange=25
		imageBth=self.filter.thresholdingMask(imageBlur,thRange)
		imageBthEroded=self.filter.thresholdingMask(image,thRange)
		imageBthCanny=self.filter.cvCanny(imageBthEroded,thRange)
		imageBthCanny=self.filter.binaryThresholding(imageBthCanny)
		imageBthCanny=cv2.dilate(imageBthCanny, None, iterations=2)
		self._saveDebugImg(imageBth,"thMask")
		self._saveDebugImg(imageBthEroded,"thMaskEroded")
		self._saveDebugImg(imageBthCanny,"thMaskCanny")
		#imageOpening=self.filter.opening(imageBth)
		#self._saveDebugImg(imageOpening,"opening")
		#imageMorphEroded=cv2.bitwise_not(imageBthEroded)
		#self._saveDebugImg(imageMorphEroded,"morphEroded")
		imageMorph=self.filter.sum(imageBthEroded,cv2.bitwise_not(imageBthCanny))
		#self._saveDebugImg(imageMorph,"morphEroded1")
		#imageMorph=self.filter.morph(imageMorph,ratio=3)
		#imageMorph=cv2.bitwise_not(imageMorph)
		self._saveDebugImg(imageMorph,"morph")
		#imageDilate=cv2.dilate(imageOpening, None, iterations=2)
		#self._saveDebugImg(imageDilate,"dilate")

		colorPoints=self.filter.analyzeImage(imageMorph)
		cont=0
		for key,item in colorPoints.items():
			if item==0:
				cont+=1
		if cont==2: #Plain image
			self._debug("**********")
			self._debug("PLAIN IMAGE DETECTED")
			self._debug("**********")
			#imageOpening=cv2.dilate(imageOpening, None, iterations=2)
			imageOpening=self.filter.close(imageMorph,ratio=3)
			imageOpening=self.filter.gaussian(imageOpening)
			#imageDistance=imageMorph
		else:
			imageOpening=imageMorph
		#imageDistance=self.filter.close(imageOpening)
		self._saveDebugImg(imageOpening,"opening")
		imageContours=self.filter.getContours(imageOpening,imageBthCanny,minWidth=200,minHeight=200)
		#imageContours=cv2.bitwise_not(imageContours)
		self._saveDebugImg(imageContours,"contours")
		imageSum=self.filter.sum(imageContours,cv2.bitwise_not(imageOpening))
		image=self.filter.gaussianAdaptative(imageSum)
		self._saveDebugImg(imageSum,"Gaussian")
		#imageErode=self.filter.erode(imageGaussian,ratio=1)
		#image=self.filter.thresholding(imageErode)
		#image=cv2.dilate(image, None, iterations=2)
		#image=self.filter.binaryThresholding(image,low=250)
		#image=self.filter.erode(image,1)
		#image=self.filter.opening(image,5)
		#image=self.filter.erode(image,2)
		#image=self.filter.close(image,4)
		#image=self.filter.erode(image,1)
		#image=self.filter.sum(imageMorph,image)
		self._saveDebugImg(imageBthEroded,"beforeEroded")
		self._saveDebugImg(cv2.bitwise_not(image),"before")
		image1=self.filter.sum(cv2.bitwise_not(image),imageBthEroded)
		image2= cv2.bitwise_xor(image, imageBthEroded)
		image= cv2.bitwise_and(image1, image2)
		#image2= self.filter.close(image2)
		#image=self.filter.sum(image,imageSum)
		self._saveDebugImg(image1,"final")
		image2=self.filter.morph(image2, 1)
		self._saveDebugImg(image2,"final2")
		image= cv2.bitwise_and(image1, image2)
		return(image)
	#def _processDarkBkgImg

	def _processLightBkgImg(self,image):
		imageBase=image
		imageMorph=self.filter.morph(image,ratio=10)
		self._saveDebugImg(imageMorph,"morph")
		#imageAnd=cv2.bitwise_and(image,imageMorph)
		#self._saveDebugImg(imageAnd,"and1")
		#imageGaussian=self.filter.gaussianAdaptative(imageAnd)
		#imageSmooth=self.filter.smooth(imageGaussian)
		imageTh=self.filter.binaryThresholding(imageSmooth)
		imageDistance=self.filter.distance(imageTh)
		self._saveDebugImg(imageDistance,"distance")
		#imageGaussian=self.filter.gaussianAdaptative(imageDistance)
		imageTh=self.filter.binaryThresholding(imageDistance,low=10)
		imageOpening=self.filter.opening(imageTh,ratio=500)
		self._saveDebugImg(imageOpening,"opening")
		imageAnd=self.filter.getContours(imageBase,imageTh)
		#imageAnd=cv2.bitwise_not(imageBase,imageOpening)
		#imageAnd=self.filter.morph(imageAnd,ratio=1)
		self._saveDebugImg(imageAnd,"and")
		#imageContours=self.filter.getContours(imageAnd,imageBase,minWidth=10,minHeight=10)
		#image=self.filter.opening(imageAnd,ratio=2)
		image=self.filter.binaryThresholding(imageAnd,low=250)
		#image=cv2.dilate(image, None, iterations=1)
		self._saveDebugImg(image,"final")
		return(image)
	#def _processLightBkgImg

	def _processAltLightBkgImg(self,image):
		imageBase=image
		imageOpening=self.filter.opening(image,ratio=2)
		self._saveDebugImg(imageOpening)
		imageGaussian=self.filter.gaussianAdaptative(imageOpening)
		imageDistance=self.filter.distance(imageGaussian)
		imageSmooth=self.filter.smooth(imageDistance)
		imageTh=self.filter.thresholding(imageSmooth,low=210,high=250)
		imageDistance=self.filter.morph(imageTh,ratio=6)
		imageContours=self.filter.getContours(imageBase,imageDistance,minWidth=105,minHeight=170)
		self._saveDebugImg(imageContours)
		imageGaussian=self.filter.gaussianAdaptative(imageContours)
		imageSmooth=self.filter.smooth(imageSmooth)
		imageTh=self.filter.thresholding(imageGaussian)
		imageContours=self.filter.getContours(imageSmooth,imageTh,minWidth=5,minHeight=5)
		image=self.filter.erode(imageContours,ratio=1)
		image=self.filter.getContours(image,imageBase,minWidth=2,minHeight=1)
		self._saveDebugImg(image)
		return(image)
	#def _processAltLightBkgImg

	def _readImg(self,imgPIL,lang="en",spellcheck=True):
		txt=""
		imgPIL=imgPIL.convert('L').resize([2 * _ for _ in imgPIL.size], Image.BICUBIC)
		imgPIL.save("/tmp/proc.png")
		self._debug("Reading with LANG {} - ".format(lang))
		txt=self._ocrProcess(imgPIL,lang)
		if txt.count(" ")>5:
			detectedLang=langid.classify(txt)
			self._debug("Detected LANGUAGE {} Spellcheck: {}".format(detectedLang[0],spellcheck))
			if detectedLang[0]!=lang:
				lang=detectedLang[0]
				txt=self._ocrProcess(imgPIL,lang)
		#txt=tesserocr.image_to_text(imgPIL,lang=tsslang)
		spellcheck==True
		if spellcheck==True:
			txt=self._hunspellCheck(txt,lang)
		return(lang,txt)
	#def _readImg

	def _ocrProcess(self,imgPIL,lang):
		txt=""
		tsslang="eng"
		if lang=="es":
			tsslang="spa"
		elif lang=="ca":
			tsslang="cat"
		try:
			api=tesserocr.PyTessBaseAPI(lang=tsslang,psm=11)
		except Exception as e:
			print(e)
			print("Switch back to va")
			ttslang="cat"
			api=tesserocr.PyTessBaseAPI(lang=tsslang,psm=11)
		api.ReadConfigFile('digits')
		# Consider having string with the white list chars in the config_file, for instance: "0123456789"
		whitelist=string.ascii_letters+string.digits+string.punctuation+string.whitespace
		api.SetVariable("classify_bln_numeric_mode", "0")
		#api.SetPageSegMode(tesserocr.PSM.DEFAULT)
		api.SetVariable('tessedit_char_whitelist', whitelist)
		api.SetImage(imgPIL)
		api.Recognize()
		txt=api.GetUTF8Text()
		self._debug((api.AllWordConfidences()))
		return(txt)
	#def _ocrProcess

	def _hunspellCheck(self,txt,lang="en"):
		dicF="/usr/share/hunspell/{}.dic".format(lang)
		if os.path.exists(dicF)==False:
			defaultLocale=locale.getdefaultlocale()
			dicF="/usr/share/hunspell/{}.dic".format(defaultLocale[0].split("_")[0])
		self._debug("Selected DICT {}".format(dicF))
		spell=hunspell.HunSpell(dicF,dicF.replace(".dic",".aff"))
		correctedTxt=[]
		for word in txt.split():
			word=word.replace("\"","")
			if word.capitalize().istitle():
				if spell.spell(word)==False:
					suggestion=spell.suggest(word)
					if len(suggestion)>0:
						word=suggestion[0]
				correctedTxt.append(word)
			else:
				onlytext = ''.join(filter(str.isalnum, word)) 
				if onlytext.capitalize().istitle():
					if spell.spell(onlytext)==False:
						suggestion=spell.suggest(onlytext)
						if len(suggestion)>0:
							onlytext=suggestion[0]
					correctedTxt.append(onlytext)
				elif self.dbg:
					self._debug("Exclude: {}".format(word))
		txt=" ".join(correctedTxt)
		return(txt)
	#def _hunspellCheck

	def _spellCheck(self,txt,lang="en"):
		spell=SpellChecker(language=lang)
		correctedTxt=[]
		for word in txt.split():
			word=word.replace("\"","")
			if word.capitalize().istitle():
				correctedTxt.append(spell.correction(word))
			else:
				onlytext = ''.join(filter(str.isalnum, word)) 
				if onlytext.capitalize().istitle():
					correctedTxt.append(spell.correction(onlytext))
				elif self.dbg:
					self._debug("Exclude: {}".format(word))
		txt=" ".join(correctedTxt)
		return(txt)
	#def _spellCheck
