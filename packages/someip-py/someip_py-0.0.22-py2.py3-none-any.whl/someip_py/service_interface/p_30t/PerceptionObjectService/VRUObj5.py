from someip_py.codec import *


class IdtVRUObjKls(SomeIpPayload):

    _include_struct_len = True

    AbsDist: Float32

    Classn: Uint8

    HozlAgLe: Float32

    HozlAgRi: Float32

    VertAgBot: Float32

    VertAgTop: Float32

    ObjTimeStamp: Float64

    ObjId: Int16

    TrkInfo: Bool

    ObjDir: Uint8

    def __init__(self):

        self.AbsDist = Float32()

        self.Classn = Uint8()

        self.HozlAgLe = Float32()

        self.HozlAgRi = Float32()

        self.VertAgBot = Float32()

        self.VertAgTop = Float32()

        self.ObjTimeStamp = Float64()

        self.ObjId = Int16()

        self.TrkInfo = Bool()

        self.ObjDir = Uint8()


class IdtVRUObj(SomeIpPayload):

    IdtVRUObj: IdtVRUObjKls

    def __init__(self):

        self.IdtVRUObj = IdtVRUObjKls()
