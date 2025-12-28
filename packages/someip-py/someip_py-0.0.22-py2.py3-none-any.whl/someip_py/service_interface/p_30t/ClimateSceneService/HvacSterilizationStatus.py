from someip_py.codec import *


class IdtHvacSterilizationSts(SomeIpPayload):

    IdtHvacSterilizationSts: Uint8

    def __init__(self):

        self.IdtHvacSterilizationSts = Uint8()
