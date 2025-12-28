from someip_py.codec import *


class IdtDispSOCLowWarn(SomeIpPayload):

    IdtDispSOCLowWarn: Uint8

    def __init__(self):

        self.IdtDispSOCLowWarn = Uint8()
