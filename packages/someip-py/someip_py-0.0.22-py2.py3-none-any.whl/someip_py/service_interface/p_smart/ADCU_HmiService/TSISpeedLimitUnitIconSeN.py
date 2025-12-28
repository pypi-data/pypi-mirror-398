from someip_py.codec import *


class TSISpeedLimitUnitIcon(SomeIpPayload):

    TSISpeedLimitUnitIcon: Uint8

    def __init__(self):

        self.TSISpeedLimitUnitIcon = Uint8()
