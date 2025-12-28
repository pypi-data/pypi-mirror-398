from someip_py.codec import *


class Time(SomeIpPayload):

    Time: Uint16

    def __init__(self):

        self.Time = Uint16()
