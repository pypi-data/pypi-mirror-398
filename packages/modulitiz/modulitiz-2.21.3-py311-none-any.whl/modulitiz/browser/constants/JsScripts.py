class JsScripts(object):
	"""
	Valori costanti contenenti codici javascript
	"""
	CHECK_PAGE_FULLY_LOADED=r"""return document.readyState;"""
	GET_WINDOW_HEIGHT=r"""return window.outerHeight;"""
	OPEN_NEW_WINDOW=r"""window.open("about:blank");"""
	SCROLL_BOTTOM=r"""window.scrollTo(0,document.body.scrollHeight);"""
	SCROLL_TOP=r"""window.scrollTo(0,document.body.scrollTop);"""
