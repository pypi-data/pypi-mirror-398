from someip_py.codec import *


class IdtTrlrDiagcKls(SomeIpPayload):

    _include_struct_len = True

    IntLowVoltSts: Uint8

    IntHighVoltSts: Uint8

    OutOpenCircuitSts: Uint8

    OutOverCircuitSts: Uint8

    LoadErrSts: Uint8

    ECUFailrGenSts: Uint8

    def __init__(self):

        self.IntLowVoltSts = Uint8()

        self.IntHighVoltSts = Uint8()

        self.OutOpenCircuitSts = Uint8()

        self.OutOverCircuitSts = Uint8()

        self.LoadErrSts = Uint8()

        self.ECUFailrGenSts = Uint8()


class IdtTrlrDiagc(SomeIpPayload):

    IdtTrlrDiagc: IdtTrlrDiagcKls

    def __init__(self):

        self.IdtTrlrDiagc = IdtTrlrDiagcKls()
