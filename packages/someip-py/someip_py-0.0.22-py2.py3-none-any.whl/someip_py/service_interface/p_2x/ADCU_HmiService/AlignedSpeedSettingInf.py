from someip_py.codec import *


class AlignedSpeedSelType(SomeIpPayload):

    AlignedSpeedSelType: Uint8

    def __init__(self):

        self.AlignedSpeedSelType = Uint8()
