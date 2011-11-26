import Live

from _Framework.ControlSurface import ControlSurface
from _Framework.MixerComponent import MixerComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.InputControlElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.EncoderElement import EncoderElement
from _Framework.SliderElement import SliderElement

from ModeSelectorComponent2 import ModeSelectorComponent2


CHAN = 0
MIXER_TRACKS = 8
SESSION_TRACKS = 8
SESSION_SCENES = 8
MODES = 4

# new names - feel free to change. row1 is top, row 4 is bottom.
BOTTOM_BUTTONS_NOTES = (38, 39, 40, 41, 42, 43, 44, 45)
SIDE_BUTTONS_NOTES = (33, 34, 35, 36)
SHIFT_BUTTON_NOTES = 37
ROW1_ENCODERS_CCS = (1, 5, 9, 13, 17, 21, 25, 29)
ROW2_ENCODERS_CCS = (2, 6, 10, 14, 18, 22, 26, 30)
ROW3_ENCODERS_CCS = (3, 7, 11, 15, 19, 23, 27, 31)
ROW4_ENCODERS_CCS = (4, 8, 12, 16, 20, 24, 28, 32)
ROW1_BUTTON_NOTES = (1, 5, 9, 13, 17, 21, 25, 29)
ROW2_BUTTON_NOTES = (2, 6, 10, 14, 18, 22, 26, 30)
ROW3_BUTTON_NOTES = (3, 7, 11, 15, 19, 23, 27, 31)
ROW4_BUTTON_NOTES = (4, 8, 12, 16, 20, 24, 28, 32)


# Factory Reset
FactoryReset = (0xf0, 0x00, 0x01, 0x61, 0x04, 0x06, 0xf7)
# Button Channel Map - 45 buttons, map all to channel 0
ButtonChannelMap = (0xf0, 0x00, 0x01, 0x61, 0x04, 0x13, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, 0xf7)
# Encoder Channel Map - 32 encoders, map all to channel 0
EncoderChannelMap = (0xf0, 0x00, 0x01, 0x61, 0x04, 0x14, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, CHAN, 0xf7)

class LinkedCode(ControlSurface):
	def __init__(self, c_instance):
		ControlSurface.__init__(self, c_instance)
		self._reset()
		# turn off rebuild MIDI map until after setup
		self.set_suppress_rebuild_requests(True)
		self._create_buttons()
		self._create_encoders()
		self._setup_mixer_control()
		self._setup_transport_control()
		self._setup_session_control()
		self._setup_mode_selector_control()
		self.set_suppress_rebuild_requests(False)

	def _reset(self):
		self._send_midi(FactoryReset)
		self._send_midi(ButtonChannelMap)
		self._send_midi(EncoderChannelMap)

	def _create_mode_buttons(self):
		self.mode_buttons = []
		for i in range(MODES):
			self.mode_buttons.append(ButtonElement(True, MIDI_NOTE_TYPE, CHAN, SIDE_BUTTONS_NOTES[MODES-1-i]))

	def _create_buttons(self):
		self._buttons = []
		for row in (ROW1_BUTTON_NOTES, ROW2_BUTTON_NOTES, ROW3_BUTTON_NOTES, ROW4_BUTTON_NOTES, BOTTOM_BUTTONS_NOTES):
			for n in row:
				self._buttons.append(ButtonElement(True, MIDI_NOTE_TYPE, CHAN, n))

	def _create_encoders(self):
		self._encoders = []
		self._sliders = []
		for row in (ROW1_ENCODERS_CCS, ROW2_ENCODERS_CCS, ROW3_ENCODERS_CCS, ROW4_ENCODERS_CCS):
			for n in row:
				self._encoders.append(EncoderElement(MIDI_CC_TYPE, CHAN, n, Live.MidiMap.MapMode.absolute))
				self._sliders.append(SliderElement(MIDI_CC_TYPE, CHAN, n))

	def _setup_mode_selector_control(self):
		self._create_mode_buttons()
		self._last_mode = -1
		self._unmap_mode_callbacks = (self._unmap_mode_0, self._unmap_mode_1, self._unmap_mode_2, self._unmap_mode_3)
		self._map_mode_callbacks = (self._map_mode_0, self._map_mode_1, self._map_mode_2, self._map_mode_3)
		self.mode_selector = ModeSelectorComponent2(MODES)
		self.mode_selector.add_mode_index_listener(self._mode_changed)
		# call this last because setting the mode buttons sets the default mode
		self.mode_selector.set_mode_buttons(tuple(self.mode_buttons))

	def _mode_changed(self):
		if self._last_mode != -1:
			self._unmap_mode_callbacks[self._last_mode]()
		self._map_mode_callbacks[self.mode_selector.mode_index]()
		self._last_mode = self.mode_selector.mode_index

	def _map_mode_0(self):
		self.log_message("+ mode 1")
		for i in range(MIXER_TRACKS):
			self.mixer.channel_strip(i).set_mute_button(self._buttons[3 * 8 + i])
			self.mixer.channel_strip(i).set_select_button(self._buttons[2 * 8 + i])
			self.mixer.channel_strip(i).set_arm_button(self._buttons[8 + i])
			self.mixer.channel_strip(i).set_solo_button(self._buttons[i])
			self.mixer.channel_strip(i).set_volume_control(self._sliders[3 * 8 + i])
			self.mixer.channel_strip(i).set_pan_control(self._encoders[2 * 8 + i])
			self.mixer.channel_strip(i).set_send_controls((self._encoders[8 + i], self._encoders[i]))
			self.mixer.channel_strip(i).set_invert_mute_feedback(True)

	def _unmap_mode_0(self):
		self.log_message("- mode 1")
		for i in range(MIXER_TRACKS):
			# self.mixer.channel_strip(i).set_shift_button(ButtonElement(True, MIDI_NOTE_TYPE, CHAN, SHIFT_BUTTON_NOTES)) # don't kwow what this does
			self.mixer.channel_strip(i).set_mute_button(None)
			self.mixer.channel_strip(i).set_select_button(None)
			self.mixer.channel_strip(i).set_arm_button(None)
			self.mixer.channel_strip(i).set_solo_button(None)
			self.mixer.channel_strip(i).set_volume_control(None)
			self.mixer.channel_strip(i).set_pan_control(None)
			self.mixer.channel_strip(i).set_send_controls(None)

	def _map_mode_1(self):
		self.log_message("mode 2 unimplemented")

	def _unmap_mode_1(self):
		self.log_message("mode 2 unimplemented")

	def _map_mode_2(self):
		self.log_message("mode 3 unimplemented")

	def _unmap_mode_2(self):
		self.log_message("mode 3 unimplemented")

	def _map_mode_3(self):
		self.log_message("mode 4 unimplemented")

	def _unmap_mode_3(self):
		self.log_message("mode 4 unimplemented")

	def _setup_mixer_control(self):
		# MixerComponent(num_tracks, num_returns, ...)
		self.mixer = MixerComponent(MIXER_TRACKS, 0, with_eqs = True, with_filters = False)
		self.mixer.set_track_offset(0)

	def _setup_transport_control(self):
		self.log_message(__name__ + " unimplemented")

	def _setup_session_control(self):
		self.session = SessionComponent(SESSION_TRACKS, SESSION_SCENES)
		self.session.name = "Session_Control"
		self.session.set_mixer(self.mixer)
		self.session._link()

		stop_track_buttons = []
		for i in range(SESSION_TRACKS):
			stop_track_buttons.append(self._buttons[i])
		self.session.set_stop_track_clip_buttons(tuple(stop_track_buttons)) #array size needs to match num_tracks  
		
	def disconnect(self):
		if self.session and self.session._is_linked():
			self.session._unlink()
		ControlSurface.disconnect(self)
