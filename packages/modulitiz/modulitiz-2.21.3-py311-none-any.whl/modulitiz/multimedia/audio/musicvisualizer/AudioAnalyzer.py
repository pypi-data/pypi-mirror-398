import math

import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pygame


def bin_search(arr, target):
	index = len(arr)//2
	minIndex = 0
	maxIndex = len(arr) - 1
	found = False

	if target < arr[0]:
		return 0
	if target > arr[len(arr) - 1]:
		return len(arr) - 1

	while not found:
		if minIndex == len(arr) - 2:
			return len(arr) - 1
		if arr[index] < target < arr[index + 1] or arr[index] == target:
			return index
		if arr[index] > target:
			maxIndex = index
		else:
			minIndex = index
		
		index = (minIndex + maxIndex) // 2

def rotate(xy, theta):
	# https://en.wikipedia.org/wiki/Rotation_matrix#In_two_dimensions
	cos_theta, sin_theta = math.cos(theta), math.sin(theta)
	
	return (
		xy[0] * cos_theta - xy[1] * sin_theta,
		xy[0] * sin_theta + xy[1] * cos_theta
	)


def translate(xy, offset):
	return xy[0] + offset[0], xy[1] + offset[1]

def clamp(minValue, maxValue, value):
	if value < minValue:
		return minValue
	if value > maxValue:
		return maxValue
	return value


class AudioAnalyzer(object):

	def __init__(self):
		# array for frequencies
		self.frequencies_index_ratio = 0
		# array of time periods
		self.time_index_ratio = 0
		# a matrix that contains decibel values according to frequency and time indexes
		self.spectrogram = None

	def load(self, filename):
		time_series, sample_rate = librosa.load(filename)  # getting information from the file
		'''
		sample_rate=librosa.get_samplerate(filename)
		stream = librosa.stream(filename,block_length=256,frame_length=4096,hop_length=1024)
		for y_block in stream:
			time_series=y_block
		'''
		
		# getting a matrix which contains amplitude values according to frequency and time indexes
		stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=2048*4))
		# converting the matrix to decibel matrix
		self.spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
		
		# getting an array of time periodic
		times = librosa.core.frames_to_time(np.arange(self.spectrogram.shape[1]), sr=sample_rate, hop_length=512, n_fft=2048*4)
		self.time_index_ratio = len(times)/times[-2]

		# getting an array of frequencies
		frequencies = librosa.core.fft_frequencies(n_fft=2048*4)
		self.frequencies_index_ratio = len(frequencies)/frequencies[-2]
	
	def show(self):
		librosa.display.specshow(self.spectrogram, y_axis='log', x_axis='time')
		
		plt.title('spectrogram')
		plt.colorbar(format='%+2.0f dB')
		plt.tight_layout()
		plt.show()

	def get_decibel(self, target_time, freq):
		return self.spectrogram[int(freq*self.frequencies_index_ratio)][int(target_time*self.time_index_ratio)]

		# returning the current decibel according to the indexes which found by binary search
		# return self.spectrogram[bin_search(self.frequencies, freq), bin_search(self.times, target_time)]

	def get_decibel_array(self, target_time, freq_arr):
		arr = []
		for f in freq_arr:
			arr.append(self.get_decibel(target_time,f))
		return arr

class AudioBar(object):

	def __init__(self, x, y, freq, color, width=50, minHeight=10, maxHeight=100, minDecibel=-80, maxDecibel=0):
		self.x, self.y, self.freq = x, y, freq
		self.color = color
		self.width, self.minHeight, self.maxHeight = width, minHeight, maxHeight
		self.height = minHeight
		self.minDecibel, self.maxDecibel = minDecibel, maxDecibel
		self.__decibel_height_ratio = (self.maxHeight - self.minHeight)/(self.maxDecibel - self.minDecibel)

	def update(self, dt, decibel):
		desired_height = decibel * self.__decibel_height_ratio + self.maxHeight
		speed = (desired_height - self.height)/0.1
		self.height += speed * dt
		self.height = clamp(self.minHeight, self.maxHeight, self.height)

	def render(self, screen):
		pygame.draw.rect(screen, self.color, (self.x, self.y + self.maxHeight - self.height, self.width, self.height))


class AverageAudioBar(AudioBar):

	def __init__(self, x, y, rng, color, width=50, minHeight=10, maxHeight=100, minDecibel=-80, maxDecibel=0):
		super().__init__(x, y, 0, color, width, minHeight, maxHeight, minDecibel, maxDecibel)
		self.rng = rng
		self.avg = 0

	def update_all(self, dt, time, analyzer):
		self.avg = 0
		for i in self.rng:
			self.avg += analyzer.get_decibel(time, i)

		self.avg /= len(self.rng)
		self.update(dt, self.avg)


class RotatedAverageAudioBar(AverageAudioBar):

	def __init__(self, x, y, rng, color, angle=0, width=50, minHeight=10, maxHeight=100, minDecibel=-80, maxDecibel=0):
		super().__init__(x, y, 0, color, width, minHeight, maxHeight, minDecibel, maxDecibel)
		self.rng = rng
		self.rect = None
		self.angle = angle


	def render(self, screen):
		pygame.draw.polygon(screen, self.color, self.rect.points)

	def render_c(self, screen, color):
		pygame.draw.polygon(screen, color, self.rect.points)

	def update_rect(self):
		self.rect = Rect(self.x, self.y, self.width, self.height)
		self.rect.rotate(self.angle)


class Rect(object):

	def __init__(self,x,y,w,h):
		self.x, self.y, self.w, self.h = x,y,w,h

		self.points = []

		self.origin = [self.w/2,0]
		self.offset = [self.origin[0] + x, self.origin[1] + y]

		self.rotate(0)

	def rotate(self, angle):

		template = [
			(-self.origin[0], self.origin[1]),
			(-self.origin[0] + self.w, self.origin[1]),
			(-self.origin[0] + self.w, self.origin[1] - self.h),
			(-self.origin[0], self.origin[1] - self.h)
		]

		self.points = [translate(rotate(xy, math.radians(angle)), self.offset) for xy in template]

	def draw(self,screen):
		pygame.draw.polygon(screen, (255,255, 0), self.points)
