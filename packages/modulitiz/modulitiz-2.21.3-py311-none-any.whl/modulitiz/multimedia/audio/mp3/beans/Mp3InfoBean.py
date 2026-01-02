import json
from json import JSONDecodeError

from modulitiz_nano.ModuloNumeri import ModuloNumeri
from modulitiz_nano.ModuloStringhe import ModuloStringhe


class Mp3InfoBean(object):
	
	def __init__(self,jsonStr:str|None,appName:str|None,versioneApp:str|None):
		if not ModuloStringhe.isEmpty(jsonStr):
			try:
				diz=json.loads(jsonStr)
				appName=diz['nome_app']
				versioneApp=diz['versione_app']
			except JSONDecodeError:
				pass
		self.appName=appName
		self.versioneApp=versioneApp
	
	def toJson(self):
		return json.dumps(self.__dict__)
	
	def isAlreadyProcessed(self,appName:str,versioneApp:str)->bool:
		if self.appName is None or self.versioneApp is None:
			return False
		return self.appName!=appName or ModuloNumeri.versionStrToInt(self.versioneApp)>=ModuloNumeri.versionStrToInt(versioneApp)
