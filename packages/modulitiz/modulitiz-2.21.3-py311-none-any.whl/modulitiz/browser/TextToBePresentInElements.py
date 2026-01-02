from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions

class TextToBePresentInElements(object):
	"""
	An expectation for checking if the given text is present in the specified elements.
	"""
	def __init__(self, locator, testo:str):
		self.locator = locator
		self.text = testo
	
	def __call__(self, driver):
		try:
			elems:list[WebElement] = expected_conditions._find_elements(driver, self.locator)
			elemsFiltered=[x for x in elems if self.text in x.text]
			return elemsFiltered
		except StaleElementReferenceException:
			return False
	
