import mutagen.id3
from mutagen.id3._frames import Frame

from modulitiz_nano.ModuloStringhe import ModuloStringhe

TEXT_ENCODING=mutagen.id3.Encoding.UTF8


def get_all_tags(nomefile:str):
	# se non e' presente l'ID3, lo creo
	try:
		tags=mutagen.id3.ID3(nomefile)
	except mutagen.id3.ID3NoHeaderError:
		tags=mutagen.id3.ID3()
	return tags

def __get_valore_tag_from_file(nomefile:str,nomeTag:str)->Frame|None:
	tags=get_all_tags(nomefile)
	return __get_valore_tag(tags,nomeTag)
def __get_valore_tag(tags,nomeTag:str)->Frame|None:
	if nomeTag not in tags:
		return None
	valore=tags[nomeTag]
	return valore

def __get_valore_tag_prefix_from_file(nomefile:str,nomeTagPrefix:str):
	tags=get_all_tags(nomefile)
	return __get_valore_tag_prefix(tags,nomeTagPrefix)
def __get_valore_tag_prefix(tags:mutagen.id3.ID3,nomeTagPrefix:str)-> Frame|None:
	trovato=False
	nomeTag=None
	for nomeTag in tags:
		if nomeTag.startswith(nomeTagPrefix):
			trovato=True
			break
	if trovato is False:
		return None
	valore=tags[nomeTag]
	return valore


#=================================================================================================================
#======================================================TITOLO=====================================================
#=================================================================================================================
def get_titolo(tags):
	return __get_valore_tag(tags,"TIT2")

def set_titolo(tags,titolo:str):
	tag=mutagen.id3.TIT2(encoding=TEXT_ENCODING, text=titolo)
	tags.add(tag)
	return tags


#=================================================================================================================
#=====================================================ARTISTA=====================================================
#=================================================================================================================
def get_artista(tags):
	return __get_valore_tag(tags,"TPE1")

def set_artista(tags,artista:str):
	tag=mutagen.id3.TPE1(encoding=TEXT_ENCODING, text=artista)
	tags.add(tag)
	return tags


#=================================================================================================================
#======================================================ANNO=======================================================
#=================================================================================================================
def get_anno(tags)->int|None:
	tag=get_anno_tag(tags)
	if tag is None:
		return None
	valore=tag.text
	if isinstance(valore,list):
		valore=valore[0].year
	return int(valore)
	
def get_anno_tag(tags):
	return __get_valore_tag(tags,"TDRC")

def set_anno(tags,anno:int):
	tag=mutagen.id3.TDRC(encoding=TEXT_ENCODING, text=str(anno))
	tags.add(tag)
	return tags


#=================================================================================================================
#============================================FOTO / COVER / COPERTINA=============================================
#=================================================================================================================

def get_foto(tags):
	tag=__get_valore_tag_prefix(tags,"APIC:")
	if tag is None:
		return tag
	# adeguo gli attributi
	tag.encoding=mutagen.id3.Encoding.LATIN1
	mime=tag.mime
	if mime=='image/jpeg':
		tag.mime='image/jpg'
	tag.type=mutagen.id3.PictureType.COVER_FRONT
	return tag

def set_foto(tags,foto):
	if foto is None:
		return tags
	tags.add(foto)
	return tags


#=================================================================================================================
#==================================================TESTO CANZONE==================================================
#=================================================================================================================
def get_testo_canzone_tag(tags):
	tag=__get_valore_tag_prefix(tags,"USLT")
	return tag
def get_testo_canzone(tags):
	tag=get_testo_canzone_tag(tags)
	if tag is None:
		return
	return tag.text

def set_testo_canzone_from_old_tag(tags,old_tag=None):
	language=None
	new_testo=""
	if old_tag is not None:
		language=old_tag.lang
		new_testo=old_tag.text
	return set_testo_canzone(tags, new_testo, language)
def set_testo_canzone(tags,new_testo:str,language:str=None):
	if new_testo is None:
		return tags
	if ModuloStringhe.isEmpty(language) or language== 'XXX':
		language='eng'
	tag=mutagen.id3.USLT(encoding=TEXT_ENCODING, lang=language, text=new_testo)
	tags.add(tag)
	return tags


#=================================================================================================================
#=====================================================COMMENTO====================================================
#=================================================================================================================
def get_commento(tags)->str|None:
	tag=__get_valore_tag_prefix(tags,"COMM:")
	if tag is None:
		return None
	testo="\n".join(tag.text)
	return testo

def set_commento(tags,testo:str):
	tag=mutagen.id3.COMM(encoding=TEXT_ENCODING, lang='ita', desc='', text=testo)
	tags.add(tag)
	return tags

def delete_commento(tags:mutagen.id3.ID3)->mutagen.id3.ID3:
	continua=True
	while continua is True:
		tag=__get_valore_tag_prefix(tags,"COMM:")
		if tag is not None:
			tags.delall(tag.FrameID)
		else:
			continua=False
	return tags
