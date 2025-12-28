from someip_py.codec import *


class IdtRoadRoughIndctKls(SomeIpPayload):

    _include_struct_len = True

    RoughExist: Bool

    RoughLevel: Uint8

    RoughDst: Float32

    RoughLength: Float32

    def __init__(self):

        self.RoughExist = Bool()

        self.RoughLevel = Uint8()

        self.RoughDst = Float32()

        self.RoughLength = Float32()


class IdtRoadRoughIndct(SomeIpPayload):

    IdtRoadRoughIndct: IdtRoadRoughIndctKls

    def __init__(self):

        self.IdtRoadRoughIndct = IdtRoadRoughIndctKls()
