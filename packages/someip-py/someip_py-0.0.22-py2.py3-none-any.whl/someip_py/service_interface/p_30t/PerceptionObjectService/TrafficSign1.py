from someip_py.codec import *


class IdtTrafficSignKls(SomeIpPayload):

    _include_struct_len = True

    AbsDist: Float32

    DetdQly: Uint8

    HozlAgLe: Float32

    HozlAgRi: Float32

    TrkInfo: Bool

    VertAgBot: Float32

    VertAgTop: Float32

    ObjTimeStamp: Float64

    ObjId: Int16

    def __init__(self):

        self.AbsDist = Float32()

        self.DetdQly = Uint8()

        self.HozlAgLe = Float32()

        self.HozlAgRi = Float32()

        self.TrkInfo = Bool()

        self.VertAgBot = Float32()

        self.VertAgTop = Float32()

        self.ObjTimeStamp = Float64()

        self.ObjId = Int16()


class IdtTrafficSign(SomeIpPayload):

    IdtTrafficSign: IdtTrafficSignKls

    def __init__(self):

        self.IdtTrafficSign = IdtTrafficSignKls()
