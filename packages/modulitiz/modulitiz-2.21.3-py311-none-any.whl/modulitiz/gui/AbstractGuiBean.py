from abc import ABC

class AbstractGuiBean(ABC):
	
	def __init__(self, window,frame_main):
		self.window=window
		
		self.frame_main=frame_main
		self.frameHeader=None
