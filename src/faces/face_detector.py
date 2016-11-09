import cv2

class FaceDetector():
	def __init__(self, haarCascadeFilePath, videoCapture):
		try:
			self.faceCascade = cv2.CascadeClassifier(haarCascadeFilePath)
		except:
			raise Exception("Error creating haar cascade classifier. Are you sure file " + haarCascadeFilePath + " exists?")
		self.videoCapture = videoCapture
		self.tickFrequency = cv2.getTickFrequency
		self.scale = 1
		self.foundFace = False
		self.resizedWidth = 1200
		self.trackedFace = None
		self.trackedFaceROI = None
		self.templateMatchingDuration = 2
		self.templateMatchingStartTime = cv2.getTickCount()
		self.templateMatchingCurrentTime = cv2.getTickCount()
		self.isTemplateMatchingRunning = False
		self.cascadeScaleFactor = 1.1
		self.cascadeMinNeighbors = 4
		self.maximumFaceSize = 0.75
		self.minimumFaceSize = 0.25
		
	def step(self):
		ret, img = self.videoCapture.read()
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		faces = self.faceCascade.detectMultiScale(gray, 1.1, 15)
		for (x,y,w,h) in faces:
			cv2.rectangle(img, (x,y), (x+w,y+h), (0,0,255),2)
			roi_gray = gray[y:y+h, x:x+h]
			roi_color = img[y:y+h, x:x+h]

		cv2.imshow('img', img)
		k = cv2.waitKey(30) & 0xff
		if k == 27:
			return False
		return True

	def limit(self, val, inf, sup):
		return max(inf,min(val,sup))

	def limit_rect(self, rect, img):
		(x,y,w,h) = rect
		(img_width, img_height) = img.shape
		limited_x = self.limit(x, 0, img_height)
		limited_y = self.limit(y, 0, img_width)
		limited_width = self.limit(w, 0, img_width-x)
		limited_height = self.limit(h, 0, img_height-y)
		return (limited_x, limited_y, limited_width, limited_height)

	def area(self, face):
		return (face[2])*(face[3])

	def largestFace(self, faces):
		if len(faces) == 0:
			return None
		largest = faces[0]
		for face in faces[1:]:
			if  self.area(face) > self.area(largest):
				largest = face
		print largest
		return largest

	def getFaceTemplate(self, face, img):
		(x, y, w, h) = face
		x = int(x + w/4) 
		y = int(y + h/4)
		w = int(w/2)
		h = int(h/2)
		template = img[y:y+h, x:x+h]
		return template

	def getROI(self, face, img):
		(x, y, w, h) = face
		roi = (int(x - w/2), int(y - h/2), int(w * 2), int(h * 2))
		(roi_x, roi_y, roi_w, roi_h) = self.limit_rect(roi, img) 
		return img[roi_y:roi_y+roi_h, roi_x:roi_x+roi_h]

	def detectCascade(self, img, roi_only=False):
		width = img.shape[0]
		if roi_only:
			search_area = self.trackedFaceROI
		else:
			search_area = img
		faces = self.faceCascade.detectMultiScale(search_area, 
			scaleFactor = self.cascadeScaleFactor,
			minNeighbors = self.cascadeMinNeighbors,
			minSize = (int(width*self.minimumFaceSize), int(width*self.minimumFaceSize)), 
			maxSize = (int(width*self.maximumFaceSize), int(width*self.maximumFaceSize))) 

		if len(faces) == 0: 
			self.foundFace = False
			self.trackedFace = None;
			return

		self.foundFace=True
		# track only the largest face 
		self.trackedFace = self.largestFace(faces)
		self.trackedFaceTemplate = self.getFaceTemplate(self.trackedFace, img)
		self.trackedFaceROI = self.getROI(self.trackedFace, img)

	def detectTemplateMatching(self, frame):
		self.templateMatchingCurrentTime = cv2.getTickCount()
		duration = self.templateMatchingCurrentTime - self.templateMatchingStartTime
		if duration > self.templateMatchingDuration or frame.rows == 0 or frame.cols == 0:
			self.foundFace = False
			self.isTemplateRunning = False
			self.templateMatchingStartTime = cv2.getTickCount()
			return

		width, height = self.trackedFaceTemplate.shape[::-1]
		match = cv2.matchTemplate(self.trackedFaceROI, self.trackedFaceTemplate, cv2.TM_SQDIFF)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
		top_left = min_loc
		bottom_right = (top_left[0] + width, top_left[1] + height)
		self.trackedFace = cv2.rectangle(top_left, bottom_right, 255, 2)
		self.trackedFaceTemplate = self.getFaceTemplate(self.trackedFace)
		self.trackedFaceROI = self.getROI(self.trackedFace)


	def resize(self, img):
		original_height = img.shape[0]
		original_width = img.shape[1]
		self.scale = float(min(self.resizedWidth, original_width)) / original_width
		return cv2.resize(img, (int(self.scale*original_width), int(self.scale*original_height)))

	def detectFace(self):
		ret, img = self.videoCapture.read()
		# reescaling if necessary, mantaining aspect ratio
		if img.shape[1] != self.resizedWidth:
			img = self.resize(img)
		# getting only gray scale components
		gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


		color = (0,0,255)
		if not self.foundFace:
			self.detectCascade(gray_img, roi_only=False) # detect on whole image (using haar cascades)
			color = (0,0,255)
		else:
			color = (0,255,0)
			self.detectCascade(gray_img, roi_only=True) # detect on ROI (using haar cascades)
			# if self.isTemplateMatchingRunning:
			# 	self.detectTemplateMatching(img) # detect using template matching
		if self.trackedFace is not None:
			if (color[1] != 0):
				cv2.rectangle(img, 
				(self.trackedFace[0], self.trackedFace[1]), 
				(self.trackedFace[0]+self.trackedFace[2], self.trackedFace[1]+self.trackedFace[3]), 
				color, 2)
		cv2.imshow('img', img)
		k = cv2.waitKey(30) & 0xff
		if k == 27:
			return False
		return True



