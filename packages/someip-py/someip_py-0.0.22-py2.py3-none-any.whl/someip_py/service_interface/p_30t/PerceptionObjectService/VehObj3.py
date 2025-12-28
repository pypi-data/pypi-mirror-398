from someip_py.codec import *


class IdtVehObjKls(SomeIpPayload):

    _include_struct_len = True

    AbsDist: Float32

    Classn: Uint8

    HozlAgLe: Float32

    HozlAgRi: Float32

    ObjDir: Uint8

    ObjHozlAgSpdLe: Float32

    ObjHozlAgSpdRi: Float32

    TrkInfo: Bool

    VertAgBot: Float32

    VertAgTop: Float32

    ObjTimeStamp: Float64

    ObjId: Int16

    def __init__(self):

        self.AbsDist = Float32()

        self.Classn = Uint8()

        self.HozlAgLe = Float32()

        self.HozlAgRi = Float32()

        self.ObjDir = Uint8()

        self.ObjHozlAgSpdLe = Float32()

        self.ObjHozlAgSpdRi = Float32()

        self.TrkInfo = Bool()

        self.VertAgBot = Float32()

        self.VertAgTop = Float32()

        self.ObjTimeStamp = Float64()

        self.ObjId = Int16()


class IdtVehObj(SomeIpPayload):

    IdtVehObj: IdtVehObjKls

    def __init__(self):

        self.IdtVehObj = IdtVehObjKls()
