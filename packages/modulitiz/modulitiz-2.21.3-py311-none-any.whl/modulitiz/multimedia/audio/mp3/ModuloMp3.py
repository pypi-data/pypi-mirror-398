import re

from modulitiz.multimedia.audio.mp3 import ModuloMp3Tags
from modulitiz.multimedia.audio.mp3.beans.Mp3InfoBean import Mp3InfoBean
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.http.ModuloHttpUtils import ModuloHttpUtils
from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime


class ModuloMp3(object):
	pass

FEATURING=" ft. "
MIN_LUNG_TESTO_CANZONE=50

# regex che contengono l'anno della canzone, bisogna usarle in ordine
REGEX_DOM_ANNO_CANZONE=(
	r'''Data di uscita.+\:.+<span class=\"[\w -]+\"\>(\d{4})</span''',
	r'''Pubblicazione\: </span><span class=\"[\w -]+\"\>(?:\d{1,2} \w+ ){0,1}(\d{4})\<''',
)
REGEX_DOM_TESTO_CANZONE=(
	r'\w+=\"YS01Ge\"\>([^<]+)</span',
)


def imposta_tag(nomefile:str,titolo:str,artista:str,anno:int,testo_canzone:str|None,
			appName:str,versioneApp:str):
	"""
	cancello tutti i tag e imposto quelli che voglio
	"""
	tags=ModuloMp3Tags.get_all_tags(nomefile)
	
	# se e' presente la copertina la tengo
	foto=ModuloMp3Tags.get_foto(tags)
	# se e' presente il testo lo tengo
	old_testo_canzone=ModuloMp3Tags.get_testo_canzone(tags)
	if old_testo_canzone is not None and len(old_testo_canzone)<MIN_LUNG_TESTO_CANZONE:
		old_testo_canzone=None
	if old_testo_canzone is not None and ModuloStringhe.isEmpty(testo_canzone):
		testo_canzone=old_testo_canzone
	# nel caso in cui non fossero presenti i tag e' giusto che vada in errore quando cerco di cancellarli
	try:
		tags=cancella_tag_from_file(nomefile)
	except Exception:
		pass
	
	# imposto i tag
	tags=ModuloMp3Tags.set_titolo(tags, titolo)
	tags=ModuloMp3Tags.set_artista(tags, artista)
	tags=ModuloMp3Tags.set_anno(tags, anno)
	tags=ModuloMp3Tags.set_foto(tags, foto)
	if testo_canzone is not None:
		tags=ModuloMp3Tags.set_testo_canzone(tags, testo_canzone)
	# scrivo alcune info
	tags=set_info_commento(tags, appName, versioneApp)
	salva_tag(tags, nomefile)

def cancella_tag_from_file(nomefile:str):
	tags=ModuloMp3Tags.get_all_tags(nomefile)
	try:
		tags.delete()
	except Exception:
		raise ExceptionRuntime("Impossibile eliminare i tag del file "+nomefile)
	tags.save(v1=0)
	return tags

def salva_tag(tags,nomefile:str):
	# rispecifico il nome del file, perche' nel caso non sia presente l'header va in errore
	tags.save(filename=nomefile,v1=2)


def set_info_commento(tags,appName:str,versioneApp:str):
	infos=Mp3InfoBean(None,appName,versioneApp)
	jsonStr=infos.toJson()
	tags=ModuloMp3Tags.delete_commento(tags)
	tags=ModuloMp3Tags.set_commento(tags, jsonStr)
	return tags


def normalizza_featuring(testo:str)->str:
	testo=testo.replace(" feat. ",FEATURING,1)		# solo la prima occorrenza
	testo=testo.replace(" Feat. ",FEATURING,1)
	testo=testo.replace(" Ft. ",FEATURING,1)
	return testo

def get_info_canzone(artista:str,titolo:str)->tuple:
	"""
	cerca le info del brano su internet
	"""
	# rimuovo i featuring
	artista=normalizza_featuring(artista)
	indFeat=artista.find(FEATURING)
	if indFeat!=-1:
		artista=artista[0:indFeat].strip()
	# rimuovo le parentesi
	indInizio=titolo.find("(")
	indFine=titolo.find(")")
	if indInizio!=-1 and indFine!=-1:
		indFine+=1
		titolo=titolo[0:indInizio].strip()+titolo[indFine:].strip()
	# compongo la query di richiesta
	canzone=artista+" "+titolo
	canzone=canzone.strip()
	# creo l'url di richiesta
	url=ModuloHttp.URL_CERCA_GOOGLE+ModuloHttpUtils.encodeUrl(canzone)
	# faccio la richiesta
	moduloHttp=ModuloHttp(url,None,False)
	moduloHttp.setUserAgent(ModuloHttp.UA_WINDOWS_FIREFOX)
	paginaWeb=moduloHttp.doGet(-1).responseBody.decode(ModuloStringhe.CODIFICA_UTF8)
	# eseguo le regex
	results=__eseguiRegex(REGEX_DOM_ANNO_CANZONE, paginaWeb,(titolo,artista))
	anno=None
	if not ModuloListe.isEmpty(results):
		anno=int(results[0])
	
	results=__eseguiRegex(REGEX_DOM_TESTO_CANZONE, paginaWeb, None)
	testo=None
	if not ModuloListe.isEmpty(results):
		righe=results[:10]
		testo="\n".join(righe)
	
	return anno,testo

def __eseguiRegex(regexes:tuple,stringa:str,errorMsgArgs: tuple|None)->list:
	"""
	se error_msg is None: prosegui in caso di errore
	"""
	trovato=False
	results=[]
	for regex in regexes:
		results=re.findall(regex,stringa)
		if not ModuloListe.isEmpty(results):
			trovato=True
			break
	if trovato is False and errorMsgArgs is not None:
		msg="Per la canzone '{}' dell'artista '{}' non e' stato trovato l'anno su internet, se presente verra' usato quello del file.".format(*errorMsgArgs)
		print("\t"+msg)
	return results
