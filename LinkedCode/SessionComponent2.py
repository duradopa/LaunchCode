from _Framework.DeviceComponent import DeviceComponent
from _Framework.SessionComponent import SessionComponent

class SessionComponent2(SessionComponent):
	def __init__(self, num_tracks, num_scenes, surface):
		self._surface = surface
		self._create_devices(num_tracks)
		SessionComponent.__init__(self, num_tracks, num_scenes)

	def _create_devices(self, num_tracks):
		self._devices = []
		for i in range(num_tracks):
			self._devices.append(DeviceComponent())

	def _change_offsets(self, track_increment, scene_increment):
		SessionComponent._change_offsets(self, track_increment, scene_increment)
		if track_increment != 0:
			self._update_device_offsets()

	def _update_device_offsets(self):
		for i in range(len(self._devices)):
			t = i + self.track_offset()
			try:
				track = self.song().tracks[i + self.track_offset()]
				self._surface.log_message("offset " + str(i) + " has " + str(len(track.devices)) + " devices")
				self._surface.log_message("1st device: " + track.devices[0].name)
				self._devices[i].set_device(track.devices[0])
			except:
				self._surface.log_message("offset " + str(i) + " out of range?")

	def device(self, index):
		return self._devices[index]
