from _Framework.ModeSelectorComponent import ModeSelectorComponent

class ModeSelectorComponent2(ModeSelectorComponent):
	def __init__(self, num_modes):
		ModeSelectorComponent.__init__(self)
		self.num_modes = num_modes

	def number_of_modes(self):
		return self.num_modes

	def update(self):
		for button in self._modes_buttons:
			if self._modes_buttons.index(button) == self._mode_index:
				button.turn_on()
			else:
				button.turn_off()
