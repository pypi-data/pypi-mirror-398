from someip_py.codec import *


class IdtCameraSelection(SomeIpPayload):

    IdtCameraSelection: Uint8

    def __init__(self):

        self.IdtCameraSelection = Uint8()
