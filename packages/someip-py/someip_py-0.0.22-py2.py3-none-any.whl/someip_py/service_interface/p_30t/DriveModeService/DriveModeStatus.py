from someip_py.codec import *


class IdtDriveMode(SomeIpPayload):

    IdtDriveMode: Uint8

    def __init__(self):

        self.IdtDriveMode = Uint8()
