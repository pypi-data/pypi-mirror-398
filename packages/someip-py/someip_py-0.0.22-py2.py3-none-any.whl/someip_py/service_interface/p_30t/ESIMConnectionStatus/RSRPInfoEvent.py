from someip_py.codec import *


class IdtRSRPInfoKls(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    RSRP: Int16

    def __init__(self):

        self.SimNo = Uint8()

        self.RSRP = Int16()


class IdtRSRPInfo(SomeIpPayload):

    IdtRSRPInfo: IdtRSRPInfoKls

    def __init__(self):

        self.IdtRSRPInfo = IdtRSRPInfoKls()
