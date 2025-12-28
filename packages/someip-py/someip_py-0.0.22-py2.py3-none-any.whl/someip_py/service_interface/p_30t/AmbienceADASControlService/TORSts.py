from someip_py.codec import *


class IdtAmbienceTORCtrl(SomeIpPayload):

    IdtAmbienceTORCtrl: Uint8

    def __init__(self):

        self.IdtAmbienceTORCtrl = Uint8()
