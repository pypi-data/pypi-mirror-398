from someip_py.codec import *


class IdtDrvrPfmncSwitch(SomeIpPayload):

    IdtDrvrPfmncSwitch: Uint8

    def __init__(self):

        self.IdtDrvrPfmncSwitch = Uint8()


class IdtOnOff(SomeIpPayload):

    IdtOnOff: Uint8

    def __init__(self):

        self.IdtOnOff = Uint8()
