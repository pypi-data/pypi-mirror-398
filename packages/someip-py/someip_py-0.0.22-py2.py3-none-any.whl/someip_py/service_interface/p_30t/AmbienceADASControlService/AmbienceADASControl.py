from someip_py.codec import *


class IdtAmbienceADASControl(SomeIpPayload):

    IdtAmbienceADASControl: Uint8

    def __init__(self):

        self.IdtAmbienceADASControl = Uint8()


class IdtAmbienceAppReturnCode(SomeIpPayload):

    IdtAmbienceAppReturnCode: Uint8

    def __init__(self):

        self.IdtAmbienceAppReturnCode = Uint8()
