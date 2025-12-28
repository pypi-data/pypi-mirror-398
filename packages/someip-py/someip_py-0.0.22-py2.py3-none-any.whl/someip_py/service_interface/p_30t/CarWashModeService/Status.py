from someip_py.codec import *


class IdtCarWashModeStatus(SomeIpPayload):

    IdtCarWashModeStatus: Uint8

    def __init__(self):

        self.IdtCarWashModeStatus = Uint8()
