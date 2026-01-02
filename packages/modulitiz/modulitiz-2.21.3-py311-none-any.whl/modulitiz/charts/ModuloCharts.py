from dash import html


class ModuloCharts(object):
	EXTERNAL_STYLESHEETS=['https://codepen.io/chriddyp/pen/bWLwgP.css',]
	DEFAULT_PLACEHOLDER='Select...'
	
	@classmethod
	def htmlFieldset(cls,titolo:str,tagInterno,maxWidth:int|None=None):
		tag=html.Span(style={'float':'left'},children=[
			html.Fieldset(style=cls.fieldsetGetCustomStile(maxWidth),children=[
				html.Legend(children=[
					titolo
				]),
				tagInterno
			])
		])
		return tag

	@staticmethod
	def htmlBrClearBoth():
		return html.Br(style={'clear':'both'})
	
	#=============================================================
	#=============================================================
	#=============================================================
	@staticmethod
	def fieldsetGetCustomStile(maxWidth:int|None=None):
		if maxWidth is None:
			maxWidth=250
		maxWidth-=15
		width=maxWidth
		return {
			'padding':'5px','borderWidth':'unset',
			'width':width,'maxWidth':maxWidth
		}
	
	@staticmethod
	def filterElementsForSelect(elems)->list:
		elems=list(set(elems))
		elems.sort()
		return elems
