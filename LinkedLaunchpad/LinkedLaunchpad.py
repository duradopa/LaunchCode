from _Framework.SessionComponent import SessionComponent
from Launchpad import Launchpad

class LinkedLaunchpad(Launchpad):
	# Get the SessionComponent to add it to linked sessions
	def _register_component(self, component):
		Launchpad._register_component(self, component)
		if isinstance(component, SessionComponent):
			self.session = component
			self.session._link()
		return None

	def disconnect(self):
		if self.session and self.session._is_linked():
			self.session._unlink()
		Launchpad.disconnect(self)
