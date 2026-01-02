import time
from abc import ABC

from selenium import webdriver

from modulitiz.browser.constants.JsScripts import JsScripts
from modulitiz.browser.enums.BrowserPageStatusEnum import BrowserPageStatusEnum
from modulitiz_nano.ModuloDate import ModuloDate
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles


class AbstractModuloBrowser(ABC):
	def __init__(self):
		super().__init__()
		self.driver:webdriver.Firefox|None=None
	
	def maximizeWindow(self):
		self.driver.maximize_window()
	
	def isPageFullyLoaded(self) -> bool:
		"""
		Controlla che tutti gli elementi siano caricati
		come ad esempio: immagini, script js, ...
		"""
		stato=self.driver.execute_script(JsScripts.CHECK_PAGE_FULLY_LOADED)
		return stato==BrowserPageStatusEnum.COMPLETE
	
	def waitUntilPageFullyLoaded(self):
		"""
		Aspetta finchè tutti gli elementi della pagina siano stati caricati
		come ad esempio: immagini, script js, ...
		"""
		maxRetries=300
		while maxRetries>0:
			if self.isPageFullyLoaded():
				return
			maxRetries-=1
			time.sleep(0.1)
	
	def reloadFirstPage(self):
		"""
		Ricarica la prima scheda
		"""
		self.driver.refresh()
	
	def saveScreenshot(self,pathDir:str):
		"""
		Save screen of entire page in archive folder
		"""
		filename=ModuloDate.dateToString(None,ModuloDate.FORMATO_DATA_ORA_NOMEFILE)+".png"
		pathFilename=ModuloFiles.pathJoin(pathDir,filename)
		if not self.driver.save_full_page_screenshot(pathFilename):
			raise ExceptionRuntime("Screenshot not saved in folder")
