from someip_py.codec import *


class IdtADAbstractCommonData(SomeIpPayload):

    IdtADAbstractCommonData: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.IdtADAbstractCommonData = SomeIpDynamicSizeArray(Uint8)
