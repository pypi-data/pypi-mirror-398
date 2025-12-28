from someip_py.codec import *


class IdtADAlertClearFaultInfSts(SomeIpPayload):

    IdtADAlertClearFaultInfSts: Uint8

    def __init__(self):

        self.IdtADAlertClearFaultInfSts = Uint8()
