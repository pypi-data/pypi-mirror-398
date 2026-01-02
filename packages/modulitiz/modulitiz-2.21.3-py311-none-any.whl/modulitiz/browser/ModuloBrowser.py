import os
import random
import re
import shutil
import time

import selenium.common
import selenium.webdriver
from selenium.common import StaleElementReferenceException
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from modulitiz.browser.AbstractModuloBrowser import AbstractModuloBrowser
from modulitiz.browser.TextToBePresentInElements import TextToBePresentInElements
from modulitiz.browser.constants.BrowserConstants import BrowserConstants
from modulitiz.browser.constants.JsScripts import JsScripts
from modulitiz.browser.enums.BrowserAddonExtensionEnum import BrowserAddonExtensionEnum
from modulitiz.browser.enums.BrowserProxyTypeEnum import BrowserProxyTypeEnum
from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric
from modulitiz_micro.sistema.ModuloEnvVars import ModuloEnvVars
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.sistema.EnvVarsEnum import EnvVarsEnum
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloBrowser(AbstractModuloBrowser):
	
	def __init__(self,cartellaGeckodriver:str):
		super().__init__()
		if ModuloSystem.isWindows():
			fullpathGeckodriver=ModuloFiles.pathJoin(cartellaGeckodriver,"geckodriver_x")
			if ModuloSystem.isSystem64bit():
				fullpathGeckodriver+="64"
			else:
				fullpathGeckodriver+="32"
			fullpathGeckodriver+=".exe"
		else:
			fullpathGeckodriver="/snap/bin/firefox.geckodriver"
		self.fullpathGeckodriver=fullpathGeckodriver
		self.pathTemp=ModuloFiles.pathJoin(ModuloSystem.getTempFolder(),"firefox_selenium")
		self.pathDirProfile=None
		self.driver:WebDriver|None=None
	
	def populate(self,percorsoCartellaFirefox:str):
		os.makedirs(self.pathTemp,exist_ok=True)
		ModuloEnvVars.add(EnvVarsEnum.PATH,percorsoCartellaFirefox,False)
	
	# =================================================================================================================
	# ======================================== INIZIALIZZAZIONE E CHIUSURA ============================================
	# =================================================================================================================
	def createDriver(self,nomefileLog:str|None,profileBrowser:selenium.webdriver.FirefoxProfile,hideWindow:bool,privateMode:bool):
		if nomefileLog is None:
			nomefileLog=ModuloSystem.getFolderNull()
		options=self.createOptions(hideWindow,privateMode)
		options.profile=profileBrowser
		# creo il driver
		self.driver=selenium.webdriver.Firefox(options,Service(self.fullpathGeckodriver,log_output=nomefileLog))
		# get real profile dir
		self.pathDirProfile=profileBrowser._profile_dir
	
	@staticmethod
	def createOptions(hideWindow:bool,privateMode:bool)->selenium.webdriver.FirefoxOptions:
		options=selenium.webdriver.FirefoxOptions()
		options.headless=hideWindow
		if not privateMode:
			return options
		options.add_argument("-private-window")
		return options
	
	def createProfile(self,cartellaProfile:str|None,permessoImmagini:int|None,noAudio:bool,grantPermissions:bool,openNewTab:bool,
			cartellaDownload:str|None,socksProxy:tuple|None,protezioneAntiTracciamento:bool,userAgent:str|None)->selenium.webdriver.FirefoxProfile:
		if cartellaProfile is None:
			profile=selenium.webdriver.FirefoxProfile()
		else:
			profile=selenium.webdriver.FirefoxProfile(cartellaProfile)
		# parametric options
		if permessoImmagini is not None:
			profile.set_preference("permissions.default.image",permessoImmagini)
		if noAudio:
			profile.set_preference("media.volume_scale", "0.0")
		if grantPermissions:
			profile.set_preference('media.navigator.permission.disabled',True)
		if openNewTab:
			profile.set_preference("browser.link.open_newwindow",3)
			profile.set_preference("browser.link.open_newwindow.restriction",0)
			profile.set_preference("browser.link.open_newwindow.override.external",3)
		if cartellaDownload is not None:
			profile.set_preference("browser.preferences.instantApply",True)
			profile.set_preference("browser.helperApps.neverAsk.saveToDisk",BrowserConstants.NEVER_ASK_SAVE_FILES)
			profile.set_preference("browser.helperApps.alwaysAsk.force",False)
			profile.set_preference("browser.helperApps.alwaysAsk.focusWhenStarting",False)
			profile.set_preference('browser.download.manager.showWhenStarting',False)
			profile.set_preference('browser.download.manager.useWindow',False)
			profile.set_preference("browser.download.panel.shown",False)
			profile.set_preference('browser.download.folderList',2)
			profile.set_preference('browser.download.dir',cartellaDownload)
		if socksProxy is not None:
			socksProxyIp,socksProxyPorta=socksProxy
			if socksProxyIp is None:
				socksProxyIp="127.0.0.1"
			profile.set_preference('network.proxy.type',BrowserProxyTypeEnum.MANUAL)
			profile.set_preference('network.proxy.socks',socksProxyIp)
			profile.set_preference('network.proxy.socks_port',socksProxyPorta)
			profile.set_preference('network.proxy.socks_version',5)
			profile.set_preference('network.proxy.socks_remote_dns',True)
		if protezioneAntiTracciamento is not None:
			profile.set_preference('privacy.trackingprotection.enabled',protezioneAntiTracciamento)
			profile.set_preference('privacy.trackingprotection.socialtracking.enabled',protezioneAntiTracciamento)
		if userAgent is not None:
			profile.set_preference("general.useragent.override",userAgent)
		return profile
	
	def closeAll(self):
		if self.driver is None:
			return
		# delete temp dir
		if os.path.exists(self.pathTemp):
			shutil.rmtree(self.pathTemp)
		# delete profile dir
		if os.path.exists(self.pathDirProfile):
			shutil.rmtree(self.pathDirProfile)
		# close driver
		self.driver.quit()
		self.driver=None
	
	# =================================================================================================================
	# ================================================= GESTIONE HTML =================================================
	# =================================================================================================================
	
	def switchIframeByCss(self,cssSelector:str,waitUntilTimeout: int|None):
		"""
		:param cssSelector: Selettore css per identificare l'elemento
		:param waitUntilTimeout: aspetta fino a n secondi se l'elemento non e' ancora disponibile, se si e' sicuri che esista sempre mettere None
		"""
		return WebDriverWait(self.driver,waitUntilTimeout).until(
			expected_conditions.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,cssSelector))
		)
	
	def switchToDefaultFrame(self):
		"""
		Ritorna al frame (o iframe) precedente.
		"""
		self.driver.switch_to.default_content()
	
	def getElementsByCss(self,cssSelector:str,waitUntilTimeout: int|None,textInside: str|None):
		"""
		:param cssSelector: Selettore css per identificare gli elementi
		:param waitUntilTimeout: aspetta fino a n secondi se gli elementi non sono ancora disponibili, se si è sicuri che esistano sempre mettere None
		:param textInside: considera anche il testo all'interno dei tag
		"""
		if textInside is not None:
			return WebDriverWait(self.driver,waitUntilTimeout).until(
				TextToBePresentInElements((By.CSS_SELECTOR,cssSelector),textInside)
			)
		if waitUntilTimeout is None:
			return self.driver.find_elements(By.CSS_SELECTOR,cssSelector)
		try:
			return WebDriverWait(self.driver,waitUntilTimeout).until(
				expected_conditions.visibility_of_element_located((By.CSS_SELECTOR,cssSelector))
			)
		except selenium.common.exceptions.TimeoutException:
			return None
	
	@staticmethod
	def isElementDisplayed(element:WebElement)->bool:
		"""
		@param element: must be attached to dom, if you query an element, then reload page and use it, it will return False
		"""
		try:
			return element.is_displayed()
		except StaleElementReferenceException:
			return False
	
	def scrollToElement(self,elementToScroll:WebElement,cssSelectorParentElementThatWillScroll:str|None):
		"""
		@param elementToScroll: must be attached to dom, if you query an element, then reload page and use it, it will throw StaleElementReferenceException
		@param cssSelectorParentElementThatWillScroll: css selector of parent element that will scroll, default window
		"""
		if cssSelectorParentElementThatWillScroll is None:
			elementThatWillScroll="window"
		else:
			elementThatWillScroll=f"document.querySelector('{cssSelectorParentElementThatWillScroll}')"
		loc=elementToScroll.location
		command="%s.scrollTo(%s,%s); %s.scrollBy(0, -150);"%(elementThatWillScroll,loc["x"],loc["y"],elementThatWillScroll)
		self.driver.execute_script(command)
		time.sleep(0.1)
	
	def goToUrl(self,url:str,maxRetries:int=3,secPausaMin:int=5,secPausaMax:int=15):
		while maxRetries>0:
			try:
				self.driver.get(url)
				maxRetries=0
			except ExceptionHttpGeneric:
				time.sleep(random.randint(secPausaMin,secPausaMax))
				maxRetries-=1
	
	def getTabTitle(self)->str:
		windowHandle=self.driver.window_handles
		# change tab
		for windowId in self.driver.window_handles:
			if windowId!=windowHandle:
				self.driver.switch_to.window(windowId)
		# get title
		time.sleep(0.2)
		nomeScheda=self.driver.title
		return nomeScheda
	
	# =================================================================================================================
	# ============================================= PROPRIETA' FINESTRA ===============================================
	# =================================================================================================================
	def get_dimensione_finestra(self)->tuple:
		size=self.driver.get_window_size()
		larghezza=size['width']
		altezza=size['height']
		return larghezza,altezza
	
	def set_dimensione_finestra(self,larghezza:int,altezza:int):
		# massimizzo la finestra per sapere le dimensioni massime
		larghezzaPrec,altezzaPrec=self.get_dimensione_finestra()
		self.maximizeWindow()
		larghezza_max,altezza_max=self.get_dimensione_finestra()
		# imposto la dimensione desiderata se non supera la dimensione massima
		if larghezza>larghezza_max or altezza>altezza_max:
			self.driver.set_window_size(larghezzaPrec,altezzaPrec)
			return
		self.driver.set_window_size(larghezza,altezza)
	
	def set_dimensione_finestra_random(self)->tuple:
		self.driver.maximize_window()
		larghezzaMax,altezzaMax=self.get_dimensione_finestra()
		larghezza=random.randint(800,larghezzaMax)
		altezza=random.randint(500,altezzaMax)
		self.set_dimensione_finestra(larghezza,altezza)
		return larghezza,altezza
	
	# =================================================================================================================
	# ================================================== ESTENSIONI ===================================================
	# =================================================================================================================
	def aggiungi_estensioni(self,cartella:str,nomefiles:list):
		# per ogni file...
		for nomefile in nomefiles:
			#...controllo che abbia la giusta estensione
			if nomefile.endswith(BrowserAddonExtensionEnum.FIREFOX) is False:
				raise ExceptionRuntime("Il file "+nomefile+" non e' riconosciuto come estensione.")
			# installo l'estensione
			percorsoNomefile=ModuloFiles.pathJoin(cartella,nomefile)
			self.driver.install_addon(percorsoNomefile,temporary=True)
	
	def get_estensione_baseurl_da_nomefile(self,nomeEstensione:str)-> str|None:
		self.apri_nuova_scheda()
		self.driver.get("about:memory")
		bottoneMisura=self.getElementsByCss('div.opsRow button#measureButton',10,None)
		bottoneMisura.click()
		
		nomeEstensione="id="+nomeEstensione
		elemento=self.getElementsByCss('span[id*="Process:extensions"]+span.kids > span.mrName', 10, nomeEstensione)
		stringaEstensione=elemento.text
		ricerca=re.search(r""", baseURL=(.+)\)""",stringaEstensione)
		if ricerca is None:
			return None
		self.chiudi_scheda_corrente()
		return ricerca.group(1)
	
	# =================================================================================================================
	# ================================================== ALERT ========================================================
	# =================================================================================================================
	def gestione_alert(self):
		WebDriverWait(self.driver,10).until(
			expected_conditions.alert_is_present()
		)
		alertWindow=self.driver.switch_to.alert
		alertWindow.accept()
	
	# =================================================================================================================
	# ============================================== GESTIONE SCHEDE ==================================================
	# =================================================================================================================
	def retrieveOpenedTabs(self)->int:
		"""
		Recupera il numero di schede aperte.
		"""
		try:
			return len(self.driver.window_handles)
		except WebDriverException:
			return 0
		
	def apri_nuova_scheda(self)->int:
		numSchedeApertePrima=len(self.driver.window_handles)
		self.driver.execute_script(JsScripts.OPEN_NEW_WINDOW)
		numSchedeAperteDopo=len(self.driver.window_handles)
		if numSchedeApertePrima==numSchedeAperteDopo:
			raise ExceptionRuntime("Non sono riuscito ad aprire una nuova scheda")
		self.driver.switch_to.window(self.driver.window_handles[-1])
		return numSchedeAperteDopo-1
	
	def chiudi_scheda_corrente(self)->int:
		self.driver.close()
		self.driver.switch_to.window(self.driver.window_handles[0])
		return 0
	
	def chiudi_scheda_corrente_se_non_vuota(self):
		self.waitUntilPageFullyLoaded()
		if ModuloStringhe.isEmpty(self.getTabTitle()):
			return
		self.chiudi_scheda_corrente()
