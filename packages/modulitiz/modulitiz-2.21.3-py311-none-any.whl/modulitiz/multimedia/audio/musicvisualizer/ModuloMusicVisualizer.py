import colorsys
import random

class ModuloMusicVisualizer(object):
	# bass, heavy_area, low_mids, high_mids
	SETTINGS_FREQUENCIES_STANDARD=[
		{"start": 50, "stop": 100, "count": 12},
		{"start": 120, "stop": 250, "count": 40},
		{"start": 251, "stop": 2000, "count": 50},
		{"start": 2001, "stop": 6000, "count": 20},
	]
	SETTINGS_FREQUENCIES_CUSTOM=[
		{"start": 30, "stop": 120, "count": 40},
		{"start": 121, "stop": 250, "count": 30},
		{"start": 251, "stop": 2000, "count": 30},
		{"start": 2001, "stop": 6000, "count": 20},
	]
	
	@staticmethod
	def randomColor():
		hue,saturation,luminosity = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
		return [int(256 * i) for i in colorsys.hls_to_rgb(hue,luminosity,saturation)]
