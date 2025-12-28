from someip_py.codec import *


class IdtInfraRedExternalParaKls(SomeIpPayload):

    _include_struct_len = True

    YawnAngle: Int32

    PitchAngle: Int32

    RollAngle: Int32

    def __init__(self):

        self.YawnAngle = Int32()

        self.PitchAngle = Int32()

        self.RollAngle = Int32()


class IdtInfraRedExternalPara(SomeIpPayload):

    IdtInfraRedExternalPara: IdtInfraRedExternalParaKls

    def __init__(self):

        self.IdtInfraRedExternalPara = IdtInfraRedExternalParaKls()
