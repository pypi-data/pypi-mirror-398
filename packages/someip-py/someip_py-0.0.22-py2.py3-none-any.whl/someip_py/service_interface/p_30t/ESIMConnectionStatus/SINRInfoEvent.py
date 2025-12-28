from someip_py.codec import *


class IdtSINRInfoKls(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SINR: Int16

    def __init__(self):

        self.SimNo = Uint8()

        self.SINR = Int16()


class IdtSINRInfo(SomeIpPayload):

    IdtSINRInfo: IdtSINRInfoKls

    def __init__(self):

        self.IdtSINRInfo = IdtSINRInfoKls()
