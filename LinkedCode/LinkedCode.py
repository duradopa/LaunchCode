import Live

from _Framework.ControlSurface import ControlSurface
from _Framework.DeviceComponent import DeviceComponent
from _Framework.MixerComponent import MixerComponent
from _Framework.TransportComponent import TransportComponent
from _Framework.InputControlElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.EncoderElement import EncoderElement
from _Framework.SliderElement import SliderElement

# XXX reuse this for now
from Code.DetailViewCntrlComponent import DetailViewCntrlComponent

from ModeSelectorComponent2 import ModeSelectorComponent2
from SessionComponent2 import SessionComponent2

CHAN = 0
MIXER_TRACKS = 8
RETURN_TRACKS = 4
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
		self._create_device_components()
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
		# hack, placeholder control so we can get to arbitrary parameters
		# in a device
		self._dummy_encoder = EncoderElement(MIDI_CC_TYPE, CHAN + 1, 0x7f, Live.MidiMap.MapMode.absolute)
		self._encoders = []
		self._sliders = []
		for row in (ROW1_ENCODERS_CCS, ROW2_ENCODERS_CCS, ROW3_ENCODERS_CCS, ROW4_ENCODERS_CCS):
			for n in row:
				self._encoders.append(EncoderElement(MIDI_CC_TYPE, CHAN, n, Live.MidiMap.MapMode.absolute))
				self._sliders.append(SliderElement(MIDI_CC_TYPE, CHAN, n))

	def _create_device_components(self):
		self._create_return_devices()
		self._create_selected_device()
		self._create_device_view_controls()

	def _create_return_devices(self):
		self._device_returns = []
		for track in self.song().return_tracks:
			device = DeviceComponent()
			try:
				device.set_device(track.devices[0])
			except:
				self.log_message("no devices on return track")
			self._device_returns.append(device)
			if len(self._device_returns) == 2:
				break

	def _create_selected_device(self):
		self._device_selected = DeviceComponent()
		self.set_device_component(self._device_selected)

	def _create_device_view_controls(self):
		self._detail_view_control = DetailViewCntrlComponent()

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
		if self.mode_selector.mode_index == 3:
			self._unmap_session_buttons()
		if self._last_mode != -1:
			self._unmap_mode_callbacks[self._last_mode]()
		self._map_mode_callbacks[self.mode_selector.mode_index]()
		if self._last_mode == -1 or self._last_mode == 3:
			self._map_session_buttons()
		self._last_mode = self.mode_selector.mode_index

	def _map_session_buttons(self):
		for i in range(MIXER_TRACKS):
			self.mixer.channel_strip(i).set_invert_mute_feedback(True)
			self.mixer.channel_strip(i).set_mute_button(self._buttons[4 * 8 + i])
			self.mixer.channel_strip(i).set_select_button(self._buttons[3 * 8 + i])
			self.mixer.channel_strip(i).set_arm_button(self._buttons[2 * 8 + i])
			self.mixer.channel_strip(i).set_solo_button(self._buttons[8 + i])

	def _unmap_session_buttons(self):
		for i in range(MIXER_TRACKS):
			self.mixer.channel_strip(i).set_mute_button(None)
			self.mixer.channel_strip(i).set_select_button(None)
			self.mixer.channel_strip(i).set_arm_button(None)
			self.mixer.channel_strip(i).set_solo_button(None)

	def _map_mode_0(self):
		self.log_message("+ mode 1")
		for i in range(MIXER_TRACKS):
			self.mixer.channel_strip(i).set_volume_control(self._sliders[3 * 8 + i])
			self.mixer.channel_strip(i).set_pan_control(self._encoders[2 * 8 + i])
			self.mixer.channel_strip(i).set_send_controls((self._encoders[8 + i], self._encoders[i]))

	def _unmap_mode_0(self):
		self.log_message("- mode 1")
		for i in range(MIXER_TRACKS):
			self.mixer.channel_strip(i).set_volume_control(None)
			self.mixer.channel_strip(i).set_pan_control(None)
			self.mixer.channel_strip(i).set_send_controls(None)

	def _map_mode_1(self):
		self.log_message("+ mode 2")
		for i in range(SESSION_TRACKS):
			self.session.device(i).set_parameter_controls((self._encoders[3 * 8 + i], self._encoders[2 * 8 + i], self._encoders[8 + i], self._encoders[i]))

	def _unmap_mode_1(self):
		self.log_message("- mode 2")
		for i in range(SESSION_TRACKS):
			self.session.device(i).set_parameter_controls(())

	def _map_mode_2(self):
		self.log_message("+ mode 3")
		for i in range(SESSION_TRACKS):
			self.session.device(i).set_parameter_controls((self._dummy_encoder, self._dummy_encoder, self._dummy_encoder, self._dummy_encoder, self._encoders[3 * 8 + i], self._encoders[2 * 8 + i], self._encoders[8 + i], self._encoders[i]))

	def _unmap_mode_2(self):
		self.log_message("- mode 3")
		for i in range(SESSION_TRACKS):
			self.session.device(i).set_parameter_controls(())

	def _map_mode_3(self):
		self.log_message("+ mode 4")
		for i in range(len(self._device_returns)):
			self._device_returns[i].set_parameter_controls((self._encoders[3 * 8 + i * 2], self._encoders[2 * 8 + i * 2], self._encoders[8 + i * 2], self._encoders[i * 2], self._encoders[3 * 8 + i * 2 + 1], self._encoders[2 * 8 + i * 2 + 1], self._encoders[8 + i * 2 + 1], self._encoders[i * 2 + 1]))
		self._device_selected.set_parameter_controls((self._encoders[3 * 8 + 2 * 2], self._encoders[2 * 8 + 2 * 2], self._encoders[8 + 2 * 2], self._encoders[2 * 2], self._encoders[3 * 8 + 2 * 2 + 1], self._encoders[2 * 8 + 2 * 2 + 1], self._encoders[8 + 2 * 2 + 1], self._encoders[2 * 2 + 1]))
		self._device_selected.set_on_off_button(self._buttons[2 * 8 + 5])
		self._detail_view_control.set_device_clip_toggle_button(self._buttons[4 * 8 + 4])
		self._detail_view_control.set_detail_toggle_button(self._buttons[4 * 8 + 5])
		self._detail_view_control.set_device_nav_buttons(self._buttons[3 * 8 + 4], self._buttons[3 * 8 + 5])
		for i in range(3):
			self.mixer.return_strip(i).set_volume_control(self._sliders[(3 - i) * 8 + 6])
		for i in range(RETURN_TRACKS):
			self.mixer.return_strip(i).set_invert_mute_feedback(True)
			self.mixer.return_strip(i).set_select_button(self._buttons[4 * 8 + i])
			self.mixer.return_strip(i).set_mute_button(self._buttons[3 * 8 + i])
		self.mixer.master_strip().set_select_button(self._buttons[4 * 8 + 6])
		self.mixer.master_strip().set_volume_control(self._sliders[3 * 8 + 7])
		self._transport.set_record_button(self._buttons[3 * 8 + 6])
		self._transport.set_play_button(self._buttons[3 * 8 + 7])
		self._transport.set_stop_button(self._buttons[2 * 8 + 7])
		self._transport.set_nudge_buttons(self._buttons[8 + 7], self._buttons[8 + 6])
		self._transport.set_tap_tempo_button(self._buttons[4 * 8 + 7])
		self._transport.set_tempo_control(self._encoders[6], self._encoders[7])

	def _unmap_mode_3(self):
		self.log_message("- mode 4")
		for i in range(len(self._device_returns)):
			self._device_returns[i].set_parameter_controls(())
		self._device_selected.set_parameter_controls(())
		self._device_selected.set_on_off_button(None)
		self._detail_view_control.set_device_clip_toggle_button(None)
		self._detail_view_control.set_detail_toggle_button(None)
		self._detail_view_control.set_device_nav_buttons(None, None)
		for i in range(3):
			self.mixer.return_strip(i).set_volume_control(None)
		for i in range(RETURN_TRACKS):
			self.mixer.return_strip(i).set_mute_button(None)
		self.mixer.master_strip().set_select_button(None)
		self.mixer.master_strip().set_volume_control(None)
		self._transport.set_record_button(None)
		self._transport.set_play_button(None)
		self._transport.set_stop_button(None)
		self._transport.set_nudge_buttons(None, None)
		self._transport.set_tap_tempo_button(None)
		self._transport.set_tempo_control(None, None)

	def _setup_mixer_control(self):
		# MixerComponent(num_tracks, num_returns, ...)
		self.mixer = MixerComponent(MIXER_TRACKS, RETURN_TRACKS, with_eqs = True, with_filters = False)
		self.mixer.set_track_offset(0)

	def _setup_transport_control(self):
		self._transport = TransportComponent()

	def _setup_session_control(self):
		self.session = SessionComponent2(SESSION_TRACKS, SESSION_SCENES, self)
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
