from someip_py.codec import *


class IdtSingleInhibitSts(SomeIpPayload):

    _include_struct_len = True

    ChrgLidID: Uint8

    InhibitSts: Uint8

    InhbTrigSrc: Uint8

    def __init__(self):

        self.ChrgLidID = Uint8()

        self.InhibitSts = Uint8()

        self.InhbTrigSrc = Uint8()


class IdtInhibitsSts(SomeIpPayload):

    IdtInhibitsSts: SomeIpDynamicSizeArray[IdtSingleInhibitSts]

    def __init__(self):

        self.IdtInhibitsSts = SomeIpDynamicSizeArray(IdtSingleInhibitSts)
