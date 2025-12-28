from someip_py.codec import *


class IdtAlarmSts(SomeIpPayload):

    IdtAlarmSts: Uint8

    def __init__(self):

        self.IdtAlarmSts = Uint8()
