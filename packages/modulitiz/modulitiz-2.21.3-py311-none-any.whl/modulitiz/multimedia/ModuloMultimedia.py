from modulitiz_binaries.Init import Init
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloMultimedia(object):
	ESTENSIONI_IMMAGINE=(".avif",".jpg",".jpeg",".png",".webp")
	ESTENSIONI_MUSICA=(".wav",".m4a",".opus",".ogg")
	ESTENSIONI_VIDEO=(".webm",".mp4",".mkv",".m4v",".3gp",".mov",".vob")
	
	ESTENSIONI=ESTENSIONI_IMMAGINE+ESTENSIONI_MUSICA+ESTENSIONI_VIDEO
	
	VIDEO_CODEC__AOMEDIA_VIDEO_1="av1"
	
	def __init__(self):
		percorsoCartella=None
		if ModuloSystem.isWindows():
			percorsoCartella=Init.getCartellaFileBinari()
		self.cartellaFileBinari=percorsoCartella
	
	def hasAudioTrack(self,nomefile:str)->bool:
		nomefileEseguibile=ModuloFiles.pathJoin(self.cartellaFileBinari, "ffprobe")
		comando=f'"{nomefileEseguibile}" -i "{nomefile}" -show_streams -select_streams a -loglevel error'
		output=ModuloSystem.systemCallReturnOutput(comando,None)
		return not ModuloStringhe.isEmpty(output)
	
	def convertImage(self,nomevecchio:str,nomenuovo:str):
		return self.convertFile(nomevecchio, nomenuovo, None,None,None,None)
	
	def convertFile(self,nomevecchio:str,nomenuovo:str,fps:int|None,larghezzaMax:int|None,altezzaMax:int|None,bitrate:str|None):
		cmdFps=""
		if fps is not None:
			cmdFps="-filter:v fps=fps="+str(fps)
		cmdDimensioni=""
		if larghezzaMax is not None:
			cmdDimensioni=f"-vf scale={larghezzaMax}:-2"
		elif altezzaMax is not None:
			cmdDimensioni=f"-vf scale=-2:{altezzaMax}"
		cmdBitrate=""
		if bitrate is not None:
			cmdBitrate="-b:a "+bitrate
		# comando
		nomefileEseguibile=ModuloFiles.pathJoin(self.cartellaFileBinari, "ffmpeg")
		comando=f'"{nomefileEseguibile}" -i "{nomevecchio}" {cmdFps} {cmdDimensioni} {cmdBitrate} "{nomenuovo}"'
		output=ModuloSystem.systemCallReturnOutput(comando,None)
		return output
	
	def getCodecName(self,nomefile:str):
		nomefileEseguibile=ModuloFiles.pathJoin(self.cartellaFileBinari, "ffprobe")
		comando=f'"{nomefileEseguibile}" -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "{nomefile}"'
		output=ModuloSystem.systemCallReturnOutput(comando,None)
		output=ModuloStringhe.normalizzaEol(output).replace("\n","")
		return output
	
	def getLengthOfVideo(self,nomefile:str):
		nomefileEseguibile=ModuloFiles.pathJoin(self.cartellaFileBinari, "ffprobe")
		comando=f'"{nomefileEseguibile}" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{nomefile}"'
		output=ModuloSystem.systemCallReturnOutput(comando,None)
		output=ModuloStringhe.normalizzaEol(output).replace("\n","")
		return float(output)
	
	def imagesToVideo(self,filesImmaginiPattern:str,nomefileVideoOut:str,fps:int):
		nomefileEseguibile=ModuloFiles.pathJoin(self.cartellaFileBinari, "ffmpeg")
		comando=f'"{nomefileEseguibile}" -framerate {fps} -i "{filesImmaginiPattern}" -c:v libx264 -pix_fmt yuv420p "{nomefileVideoOut}"'
		output=ModuloSystem.systemCallReturnOutput(comando,None)
		return output
