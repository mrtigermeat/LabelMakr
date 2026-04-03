from pygame import mixer

class mixer_wrapper:
	def __init__(self):
		'''
		Silly class for forcing pygame mixer to work better lol
		'''
		self.is_paused = False
		self.hit_play = False
		mixer.init()

	def load(self, audio):
		mixer.music.load(audio)
		self.hit_play = False

	def play(self):
		mixer.music.play()
		self.hit_play = True

	def pause(self):
		if self.hit_play:
			if self.is_paused:
				mixer.music.unpause()
				self.is_paused = False
			elif not self.is_paused:
				mixer.music.pause()
				self.is_paused = True

	def stop(self):
		mixer.music.stop()
		self.hit_play = False

	@property
	def busy(self) -> bool:
		return mixer.music.get_busy()