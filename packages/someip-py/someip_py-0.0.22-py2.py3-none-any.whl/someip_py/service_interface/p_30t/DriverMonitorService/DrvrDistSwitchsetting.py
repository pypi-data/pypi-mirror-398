from someip_py.codec import *


class IdtDrvrDistSwitch(SomeIpPayload):

    IdtDrvrDistSwitch: Uint8

    def __init__(self):

        self.IdtDrvrDistSwitch = Uint8()


class IdtOnOff(SomeIpPayload):

    IdtOnOff: Uint8

    def __init__(self):

        self.IdtOnOff = Uint8()
