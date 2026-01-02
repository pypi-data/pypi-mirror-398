import tkinter
from tkinter import ttk
from tkinter.font import Font

from modulitiz.gui.componenti import Bottone
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime

MIN_SIZE_WINDOW=(300,200)

DEFAULT_FONT=None

'''
=================================GESTIONE FINESTRA=================================
'''

def crea_finestra(titolo:str,centerWindow:bool,percorsoIcona:str):
	global DEFAULT_FONT
	
	window=tkinter.Tk()
	DEFAULT_FONT=getDefaultFont()
	# dimensione minima
	window.minsize(*MIN_SIZE_WINDOW)
	# posizione finestra
	if centerWindow is True:
		center_finestra(window)
	# titolo
	setTitoloFinestra(window, titolo)
	# icona
	if percorsoIcona is not None:
		if percorsoIcona.endswith(".ico") is False:
			raise ExceptionRuntime("L'icona deve avere estensione .ico")
		window.iconbitmap(percorsoIcona)
	return window

def set_dimensione_finestra(window:tkinter.Tk, larg:int, alt:int):
	window.geometry("%dx%d"%(larg,alt))

def setTitoloFinestra(window, titolo:str):
	window.title(titolo)

def center_finestra(window):
	window.update_idletasks()

	# Tkinter way to find the screen resolution
	screen_width = window.winfo_screenwidth()
	screen_height = window.winfo_screenheight()
	
	size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
	num_pixel_x = int(screen_width/2 - size[0]/2)
	num_pixel_y = int(screen_height/2 - size[1]/2)
	
	window.geometry("+%d+%d" % (num_pixel_x, num_pixel_y))

def chiudi_finestra(window):
	window.destroy()


#=================================================================================================================
#=================================================GESTIONE FRAME==================================================
#=================================================================================================================
def crea_frame(window) -> tkinter.Frame:
	frame = tkinter.Frame(window)
	return frame


#=================================================================================================================
#==============================================FUNZIONI COMPONENTI================================================
#=================================================================================================================
def crea_testo(frame,testo:str,font=None,wrapLength=None):
	label=tkinter.Label(frame,text=testo,wraplength=wrapLength)
	if font is not None:
		label['font']=font
	label.pack()
	return label

def crea_bottone(frame,testo:str, funzione_on_click,*args,**kwargs)->tkinter.Button:
	bottone=tkinter.Button(frame,text=testo,relief=Bottone.TipoBordo.rigaSemplice)
	bottone.configure(command=(lambda btn=bottone: funzione_on_click(btn,*args,**kwargs)))
	bottone['font'] = DEFAULT_FONT
	# stile
	bottone["bg"] = "white"
	bottone.pack()
	return bottone

def get_bottone_testo(bottone:tkinter.Button)->tkinter.Button:
	return bottone.cget("text")

def hr(frame)->ttk.Separator:
	separator = ttk.Separator(frame, orient='horizontal')
	separator.pack(side='top', fill='x')
	return separator


#=================================================================================================================
#======================================================ALTRO======================================================
#=================================================================================================================
def getDefaultFont()->Font:
	font=Font(size=12)
	return font
def getFontH1()->Font:
	font=Font(size=20)
	return font
def getFontH2()->Font:
	font=Font(size=17)
	return font
