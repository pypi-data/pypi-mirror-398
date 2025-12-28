from someip_py.codec import *


class IdtDayOrNightSts(SomeIpPayload):

    IdtDayOrNightSts: Uint8

    def __init__(self):

        self.IdtDayOrNightSts = Uint8()
