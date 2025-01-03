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
from PySide2.QtGui import QClipboard
try:
	from . import kconfig
except:
	import kconfig

class filters():
	def __init__(self,*args,**kwargs):
		self.dbg=True

	def process(self,image):
		# load the input image and grab the image dimensions
		orig = image.copy()
		(H, W) = image.shape[:2]
		layerNames = [
			"feature_fusion/Conv_7/Sigmoid",
			"feature_fusion/concat_3"]
		# load the pre-trained EAST text detector
		print("[INFO] loading EAST text detector...")
		net = cv2.dnn.readNet("frozen_east_text_detection.pb")
		# construct a blob from the image and then perform a forward pass of
		# the model to obtain the two output layer sets
		blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
			(123.68, 116.78, 103.94), swapRB=True, crop=False)
		start = time.time()
		net.setInput(blob)
		(scores, geometry) = net.forward(layerNames)
		end = time.time()
		# show timing information on text prediction
		print("[INFO] text detection took {:.6f} seconds".format(end - start))
		# grab the number of rows and columns from the scores volume, then
		# initialize our set of bounding box rectangles and corresponding
		# confidence scores
		(numRows, numCols) = scores.shape[2:4]
		rects = []
		confidences = []
		# loop over the number of rows
		for y in range(0, numRows):
			# extract the scores (probabilities), followed by the geometrical
			# data used to derive potential bounding box coordinates that
			# surround text
			scoresData = scores[0, 0, y]
			xData0 = geometry[0, 0, y]
			xData1 = geometry[0, 1, y]
			xData2 = geometry[0, 2, y]
			xData3 = geometry[0, 3, y]
			anglesData = geometry[0, 4, y]
		# loop over the number of columns
		for x in range(0, numCols):
			# if our score does not have sufficient probability, ignore it
			if scoresData[x] < args["min_confidence"]:
				continue
			# compute the offset factor as our resulting feature maps will
			# be 4x smaller than the input image
			(offsetX, offsetY) = (x * 4.0, y * 4.0)
			# extract the rotation angle for the prediction and then
			# compute the sin and cosine
			angle = anglesData[x]
			cos = np.cos(angle)
			sin = np.sin(angle)
			# use the geometry volume to derive the width and height of
			# the bounding box
			h = xData0[x] + xData2[x]
			w = xData1[x] + xData3[x]
			# compute both the starting and ending (x, y)-coordinates for
			# the text prediction bounding box
			endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
			endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
			startX = int(endX - w)
			startY = int(endY - h)
			# add the bounding box coordinates and probability score to
			# our respective lists
			rects.append((startX, startY, endX, endY))
			confidences.append(scoresData[x])
		# apply non-maxima suppression to suppress weak, overlapping bounding
		# boxes
		boxes = non_max_suppression(np.array(rects), probs=confidences)
		# loop over the bounding boxes
		for (startX, startY, endX, endY) in boxes:
			# scale the bounding box coordinates based on the respective
			# ratios
			startX = int(startX * rW)
			startY = int(startY * rH)
			endX = int(endX * rW)
			endY = int(endY * rH)
			# draw the bounding box on the image
			cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
		return(orig)




	def resize(self,image):
		return(cv2.resize(image, None,fx=2.0,fy=2.0))
	#def resize

	def opening(self,image):
		kernel = np.ones((7,7),np.uint8)
		return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

	def thresholding(self,image):
		#return(cv2.threshold(image, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1])
		return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

	def distance(self,image):
		image=cv2.distanceTransform(image,cv2.DIST_L2,5)
		image=cv2.normalize(image, image, 0, 1.0, cv2.NORM_MINMAX)
		image=(image * 255).astype("uint8")
		image=self.thresholding(image)
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
		opening=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
		image=cv2.morphologyEx(image, cv2.MORPH_OPEN,opening)
		return(image)

	def getContours(self,image,image2):
		# find contours in the opening image, then initialize the list of
		# contours which belong to actual characters that we will be OCR'ing
		cnts=cv2.findContours(image.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		cnts2=cv2.findContours(image2.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		chars = []
		# loop over the contours
		for c in cnts:
			print("C: {}".format(c))
		# compute the bounding box of the contour
			(x, y, w, h) = cv2.boundingRect(c)
			# check if contour is at least 35px wide and 100px tall, and if
			# so, consider the contour a digit
			if w >= 55 and h >= 120:
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
		return cv2.bitwise_or(image, image2, mask=mask)

	def blur(self,image):
		kernel = np.ones((5,5),np.uint8)
		dilation = cv2.dilate(image,kernel,iterations =5)
		blur =cv2.GaussianBlur(dilation,(3,3),0)
		image= cv2.erode(blur,kernel,iterations =5)
		image=cv2.Canny(image,100,200)
		return(image)
	#def blur(self,image):
	
	def cvGrayscale(self,image):
		return(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))

	#canny edge detection
	def cvCanny(self,image):
		return cv2.Canny(image, 100, 200)

	def smooth(self,image):
		return cv2.bilateralFilter(image,15,50,50)

	def gaussianAdaptative(self,image):
		blur=cv2.GaussianBlur(image,(5,5),0)
		ret3,image = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		return(image)

	def gaussian(self,image):
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
		txt=""
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
			lang,txt=self._readImg(imgPIL,lang=lang,spellcheck=spellcheck)
		return(lang,txt)
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
			else:
				img=self.clipboard.pixmap()
				if img:
					self._debug("Reading clipboard PXM")
					img.save(outImg, "PNG")
		if img==None and onlyClipboard==False:
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
		#image=self.filter.process(image)
		image=self.filter.cvGrayscale(image)
		image=self.filter.resize(image)
		cv2.imwrite(outImg.replace(".png","10.png"),image)
		image2=self.filter.thresholding(image)
		cv2.imwrite(outImg.replace(".png","15.png"),image2)
		#image=self.filter.thresholding(image)
		#cv2.imwrite(outImg.replace(".png","15.png"),image)
		#image=self.filter.gaussianAdaptative(image)
		#image=self.filter.opening(image)
		#image=self.filter.blur(image)
		#image=self.filter.distance(image)
		image=self.filter.morph(image)
		cv2.imwrite(outImg.replace(".png","20.png"),image)
		#image=self.filter.gaussianAdaptative(image)
		#image=self.filter.smooth(image)
		image=self.filter.thresholding(image)
		cv2.imwrite(outImg.replace(".png","30.png"),image)
		image=self.filter.getContours(image,image2)
		image=self.filter.gaussianAdaptative(image)
		#image=self.filter.cvCanny(image)
		cv2.imwrite(outImg.replace(".png","40.png"),image)
######
#REM
#grayscale
#morph
#thresh
#getcont
######
		# <- END
		self._debug("Saving processed img as {}".format(outImg))
		cv2.imwrite(outImg,image)
		return(outImg)
	#def _processImg

	def _readImg(self,imgPIL,lang="en",spellcheck=True):
		txt=""
		imgPIL=imgPIL.convert('L').resize([5 * _ for _ in imgPIL.size], Image.BICUBIC)
		imgPIL.save("/tmp/proc.png")
		self._debug("Reading with LANG {} - ".format(lang))
		txt=self._ocrProcess(imgPIL,lang)
		if txt.count(" ")>5:
			detectedLang=langid.classify(txt)
			self._debug("Detected LANGUAGE {}".format(detectedLang[0]))
			if detectedLang[0]!=lang:
				lang=detectedLang[0]
				txt=self._ocrProcess(imgPIL,lang)
		#txt=tesserocr.image_to_text(imgPIL,lang=tsslang)
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
