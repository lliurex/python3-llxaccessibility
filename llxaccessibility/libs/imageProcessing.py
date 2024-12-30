#!/usr/bin/python3
import tesserocr
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
from PySide2.QtGui import QClipboard
import speechd
try:
	from . import kconfig
except:
	import kconfig

class filters():
	def __init__(self,*args,**kwargs):
		self.dbg=True

	def opening(self,image):
		kernel = np.ones((5,5),np.uint8)
		return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

	def thresholding(self,image):
		return(cv2.threshold(image, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1])
		#return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

	def distance(self,image):
		image=cv2.distanceTransform(image,cv2.DIST_L2,5)
		image=cv2.normalize(image, image, 0, 1.0, cv2.NORM_MINMAX)
		image=(image * 255).astype("uint8")
		return(image)

	def sobel(self,image):
		img = cv2.cvtColor(
			src=image,
			code=cv2.COLOR_RGB2GRAY,
		)

		dx, dy = 1, 0
		img_sobel = cv2.Sobel(
			src=img,
			ddepth=cv2.CV_64F,
			dx=dx,
			dy=dy,
			ksize=5,
		)
		return(img_sobel)
		 
	def morph(self,image):
		opening=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
		image=cv2.morphologyEx(image, cv2.MORPH_OPEN,opening)
		return(image)

	def getContours(self,image):
		# find contours in the opening image, then initialize the list of
		# contours which belong to actual characters that we will be OCR'ing
		cnts=cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		chars = []
		# loop over the contours
		for c in cnts:
		# compute the bounding box of the contour
			(x, y, w, h) = cv2.boundingRect(c)
			# check if contour is at least 35px wide and 100px tall, and if
			# so, consider the contour a digit
			if w >= 5 and h >= 10:
				chars.append(c)
		# compute the convex hull of the characters
		chars = np.vstack([chars[i] for i in range(0, len(chars))])
		hull = cv2.convexHull(chars)
		# allocate memory for the convex hull mask, draw the convex hull on
		# the image, and then enlarge it via a dilation
		mask = np.zeros(image.shape[:2], dtype="uint8")
		cv2.drawContours(mask, [hull], -1, 255, -1)
		mask = cv2.dilate(mask, None, iterations=2)
		# take the bitwise of the opening image and the mask to reveal *just*
		# the characters in the image
		return(cv2.bitwise_and(image, image, mask=mask))
	
	# get grayscale image
	def cvGrayscale(self,image):
		return(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY))

	#canny edge detection
	def cvCanny(self,image):
		return cv2.Canny(image, 100, 200)

	def smooth(self,image):
		return cv2.bilateralFilter(image,9,75,75)

	def gaussian(self,image):
		img_gaussian = cv2.GaussianBlur(
			src=image,
			ksize=(5, 5),
			sigmaX=0,
			sigmaY=0,
		)
		return(img_gaussian)

	#skew correction
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

class imageProcessing():
	def __init__(self,parent=None):
		self.dbg=True
		self.filter=filters()
		self.clipboard=QClipboard()
		self.kconfig=kconfig.kconfig()
	#def __init__(self,parent=None):

	def _debug(self,msg):
		if self.dbg==True:
			print("imageProcessing: {}".format(msg))
	#def _debug
	
	def getImageOCR(self,spellcheck=True,onlyClipboard=False,onlyScreen=False,lang="en"):
		img=self._getImgForOCR(onlyClipboard,onlyScreen)
		imgPIL=None
		if os.path.isfile(img):
			img=self._processImg(img)
			try:
				imgPIL = Image.open(img)
				self._debug("Opened IMG. Waiting OCR")
			except Exception as e:
				print(e)
		if imgPIL:
			txt=self._readImg(imgPIL,lang=lang,spellcheck=spellcheck)
		return(txt)
	#def getImageOCR

	def _getImgForOCR(self,onlyClipboard=False,onlyScreen=False):
		cfg=self.kconfig.getTTSConfig()
		outImg="/tmp/out.png"
		img=None
		if onlyScreen==False:
			img=self.clipboard.image()
			if img:
				self._debug("Reading clipboard IMG")
				img.save(outImg, "PNG")
		elif onlyScreen==False:
			img=self.clipboard.pixmap()
			if img:
				self._debug("Reading clipboard PXM")
				img.save(outImg, "PNG")
		elif onlyClipboard==False:
			self._debug("Taking Screenshot")
			if cfg.get("Screenshot",False)==False:
				subprocess.run(["spectacle","-a","-e","-b","-c","-o",outImg])
			else:
				subprocess.run(["spectacle","-r","-e","-b","-c","-o",outImg])
		return(outImg)
	#def _getImgForOCR

	def _processImg(self,img):
		cfg=self.kconfig.getTTSConfig()
		imgFilter=self.kconfig.getTextFromValueKScript("ocrwindow","filter",cfg.get("filter",0))
		self._debug("Postprocessing img with {} filter".format(imgFilter))
		outImg="{}".format(img)
		image=cv2.imread(img,flags=cv2.IMREAD_COLOR)
		#h, w, c = image.shape
		#self._debug(f'Image shape: {h}H x {w}W x {c}C')
	#	image = image[:, :, 1]
#		if "grayscale" in imgFilter.lower():
#			image=self.filter.cvGrayscale(image)
#		elif "sobel" in imgFilter.lower():
#			image=self.filter.sobel(image)
#		elif "threshold" in imgFilter.lower():
#			image=self.filter.thresholding(image)
#		elif "deskew" in imgFilter.lower():
#			image=self.filter.cvDeskew(image)
#		elif "opening" in imgFilter.lower():
#			image=self.filter.opening(image)
#		elif "smooth" in imgFilter.lower():
#			image=self.filter.smooth(image)
#		elif "canny" in imgFilter.lower():
#			image=self.filter.cvCanny(image)
		# From pyimage doc 
		image=self.filter.cvGrayscale(image)
		image=self.filter.thresholding(image)
		image=self.filter.distance(image)
		image=self.filter.thresholding(image)
		image=self.filter.morph(image)
		image=self.filter.getContours(image)
		# <- END
		self._debug("Saving processed img as {}".format(outImg))
		cv2.imwrite(outImg,image)
		return(outImg)
	#def _processImg

	def _readImg(self,imgPIL,lang="en",spellcheck=True):
		txt=""
		tsslang="eng"
		if lang=="es":
			tsslang="spa"
		elif lang=="ca":
			tsslang="cat"

		imgPIL=imgPIL.convert('L').resize([5 * _ for _ in imgPIL.size], Image.BICUBIC)
		imgPIL.save("/tmp/proc.png")
		self._debug("Reading with LANG {} - ".format(tsslang,lang))
		with tesserocr.PyTessBaseAPI(lang=tsslang,psm=11) as api:
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
		#txt=tesserocr.image_to_text(imgPIL,lang=tsslang)
		if spellcheck==True:
			txt=self._hunspellCheck(txt,lang)
		return(txt)
	#def _readImg

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
