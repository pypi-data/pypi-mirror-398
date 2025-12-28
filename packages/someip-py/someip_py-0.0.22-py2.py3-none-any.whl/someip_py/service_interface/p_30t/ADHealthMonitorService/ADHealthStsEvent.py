from someip_py.codec import *


class IdtADHealthStsKls(SomeIpPayload):

    _include_struct_len = True

    FuncCtrlSts: Uint8

    Timestamp: Uint64

    def __init__(self):

        self.FuncCtrlSts = Uint8()

        self.Timestamp = Uint64()


class IdtADHealthSts(SomeIpPayload):

    IdtADHealthSts: IdtADHealthStsKls

    def __init__(self):

        self.IdtADHealthSts = IdtADHealthStsKls()
