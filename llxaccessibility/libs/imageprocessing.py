#!/usr/bin/python3
import tesserocr
from spellchecker import SpellChecker
import hunspell
import locale
import subprocess
import string
import os
import cv2
import numpy as np
from PIL import Image
from PySide2.QtGui import QClipboard

class filters():
	def __init__(self,*args,**kwargs):
		self.dbg=True

	def opening(self,img):
		kernel = np.ones((5,5),np.uint8)
		return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

	def thresholding(self,image):
		return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

	def sobel(self,img):
		img = cv2.cvtColor(
			src=img,
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
		 
	def morph(self,img):
####	op = cv2.MORPH_OPEN
####	img_morphology = cv2.morphologyEx(
####		src=img,
####		op=op,
####		kernel=np.ones((5, 5), np.uint8),
####	)
		op = cv2.MORPH_CLOSE
		img_morphology = cv2.morphologyEx(
			src=img_morphology,
			op=op,
			kernel=np.ones((5, 5), np.uint8),
		)
		return(img_morphology)
	
	# get grayscale image
	def cvGrayscale(self,image):
		return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

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

class imageprocessing():
	def __init__(self,parent=None):
		self.dbg=True
		self.filter=filters()
		self.clipboard=QClipboard()
	#def __init__(self,parent=None):

	def _debug(self,msg):
		if self.dbg==True:
			print("imageProcessing: {}".format(msg))
	#def _debug
	
	def _processImg(self,img):
		outImg="{}".format(img)
		image=cv2.imread(img,flags=cv2.IMREAD_COLOR)
		h, w, c = image.shape
		#self._debug(f'Image shape: {h}H x {w}W x {c}C')

	#	image = image[:, :, 0]
		image=self.filter.cvGrayscale(image)
	#	image=self.sobel(image)
	#	image=self.thresholding(image)
	#	image=self.cvDeskew(image)
	#	image=self.opening(image)
	#	image=self.smooth(image)
	#	image=self.cvCanny(image)
		self._debug("Saving processed img as {}".format(outImg))
		cv2.imwrite(outImg,image)
		return(outImg)
	#def _processImg

	def _getImgForOCR(self,onlyClipboard=False,onlyScreen=False):
		outImg="/tmp/out.png"
		img=None
		if onlyScreen==False:
			img=self.clipboard.image()
		if img:
			self._debug("Reading clipboard IMG")
			img.save(outImg, "PNG")
		else:
			if onlyScreen==False:
				img=self.clipboard.pixmap()
			if img:
				self._debug("Reading clipboard PXM")
				img.save(outImg, "PNG")
			elif onlyClipboard==False:
				self._debug("Taking Screenshot")
				subprocess.run(["spectacle","-a","-e","-b","-c","-o",outImg])
		return(outImg)
	#def _getImgForOCR

	def _readImg(self,imgPIL,lang="en"):

		txt=""
		if lang=="en":
			tsslang="eng"
		elif lang=="es":
			tsslang="spa"
		elif lang=="ca":
			tsslang="cat"

		imgPIL=imgPIL.convert('L').resize([5 * _ for _ in imgPIL.size], Image.BICUBIC)
		imgPIL.save("/tmp/proc.png")
		print("Reading with {}".format(tsslang))
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
		#txt=tesserocr.image_to_text(imgPIL,lang="spa")
		txt=self._hunspellCheck(txt,lang)
		return(txt)
	#def _readImg

	def getImageOCR(self,onlyClipboard=False,onlyScreen=False,lang="en"):
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
			txt=self._readImg(imgPIL,lang=lang)
		return(txt)
	#def getImageOCR

	def _hunspellCheck(self,txt,lang="en"):
		dicF="/usr/share/hunspell/{}.dic".format(lang)
		if os.path.exists(dicF)==False:
			defaultLocale=locale.getDefaultLocale()
			dicF="/usr/share/hunspell/{}.dic".format(defaultLocale[0].split("_")[0])
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
