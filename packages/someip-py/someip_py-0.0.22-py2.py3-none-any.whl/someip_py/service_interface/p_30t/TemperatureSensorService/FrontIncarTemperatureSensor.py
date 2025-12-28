from someip_py.codec import *


class IdtClimaTSnsrKls(SomeIpPayload):

    _include_struct_len = True

    CmptmtTempDetn: Float32

    CmptmtTempDetnQf: Bool

    def __init__(self):

        self.CmptmtTempDetn = Float32()

        self.CmptmtTempDetnQf = Bool()


class IdtClimaTSnsr(SomeIpPayload):

    IdtClimaTSnsr: IdtClimaTSnsrKls

    def __init__(self):

        self.IdtClimaTSnsr = IdtClimaTSnsrKls()
