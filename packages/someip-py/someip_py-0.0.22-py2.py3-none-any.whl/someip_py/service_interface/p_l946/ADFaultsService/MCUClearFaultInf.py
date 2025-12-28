from someip_py.codec import *


class IdtADMCUAlertClearFaultInfSts(SomeIpPayload):

    IdtADMCUAlertClearFaultInfSts: Uint8

    def __init__(self):

        self.IdtADMCUAlertClearFaultInfSts = Uint8()
