from someip_py.codec import *


class IdtSettingRst(SomeIpPayload):

    IdtSettingRst: Uint8

    def __init__(self):

        self.IdtSettingRst = Uint8()
