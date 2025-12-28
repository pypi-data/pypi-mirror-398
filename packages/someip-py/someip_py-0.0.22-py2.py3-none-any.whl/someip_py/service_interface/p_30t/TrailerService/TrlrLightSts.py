from someip_py.codec import *


class IdtTrlrLampSts(SomeIpPayload):

    _include_struct_len = True

    TrlrLampID: Uint8

    TrlrOnOff: Uint8

    def __init__(self):

        self.TrlrLampID = Uint8()

        self.TrlrOnOff = Uint8()


class IdtTrlrLampsSts(SomeIpPayload):

    IdtTrlrLampsSts: SomeIpDynamicSizeArray[IdtTrlrLampSts]

    def __init__(self):

        self.IdtTrlrLampsSts = SomeIpDynamicSizeArray(IdtTrlrLampSts)
