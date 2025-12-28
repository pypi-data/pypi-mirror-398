from someip_py.codec import *


class IdtCamFltsStsToADCU(SomeIpPayload):

    IdtCamFltsStsToADCU: Uint8

    def __init__(self):

        self.IdtCamFltsStsToADCU = Uint8()
