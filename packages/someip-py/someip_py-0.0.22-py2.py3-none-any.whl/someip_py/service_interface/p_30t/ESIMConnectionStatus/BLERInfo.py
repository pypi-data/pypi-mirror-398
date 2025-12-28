from someip_py.codec import *


class IdtBLERInfoKls(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    BLER: Uint8

    def __init__(self):

        self.SimNo = Uint8()

        self.BLER = Uint8()


class IdtBLERInfo(SomeIpPayload):

    IdtBLERInfo: IdtBLERInfoKls

    def __init__(self):

        self.IdtBLERInfo = IdtBLERInfoKls()
