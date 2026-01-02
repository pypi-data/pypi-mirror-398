import tkinter as tk


class VerticalScrolledFrame(tk.Frame):
	"""A pure Tkinter scrollable frame that actually works!
	
	* Use the 'interior' attribute to place widgets inside the scrollable frame
	* Construct and pack/place/grid normally
	* This frame only allows vertical scrolling
	"""
	
	def __init__(self, parent:tk.Frame, *args, **kw):
		tk.Frame.__init__(self, parent, *args, **kw)
		
		# create a canvas object and a vertical scrollbar for scrolling it
		vscrollbar=tk.Scrollbar(self, orient=tk.VERTICAL)
		vscrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
		canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
		canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		vscrollbar.config(command=canvas.yview)
		# quando la finestra cambia dimensione anche il frame si adatta
		self.pack(fill=tk.BOTH, expand=True)
		
		# reset the view
		canvas.xview_moveto(0)
		canvas.yview_moveto(0)
		
		# create a frame inside the canvas which will be scrolled with it
		self.interior = tk.Frame(canvas)
		self.__interiorId = canvas.create_window(0, 0, window=self.interior, anchor=tk.NW)
		self.canvas=canvas
		
		self.interior.bind('<Configure>', self.__configureInterior)
		self.canvas.bind('<Configure>', self.__configureCanvas)
	
	def __configureInterior(self,_event):
		"""
		Track changes to the canvas and frame width and sync them, also updating the scrollbar
		"""
		width=self.interior.winfo_reqwidth()
		if width==1:
			return
		height=self.interior.winfo_reqheight()
		scrollRegion=(0,0,width,height)
		# update the scrollbars to match the size of the inner frame
		self.canvas.config(scrollregion=scrollRegion,yscrollincrement=15)
	
	def __configureCanvas(self,_event):
		if self.interior.winfo_reqwidth() == self.canvas.winfo_width():
			return
		# update the inner frame's width to fill the canvas
		self.canvas.itemconfigure(self.__interiorId, width=self.canvas.winfo_width())
