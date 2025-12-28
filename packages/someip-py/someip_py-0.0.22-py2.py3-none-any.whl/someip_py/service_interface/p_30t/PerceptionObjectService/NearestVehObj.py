from someip_py.codec import *


class IdtNearestVehObjKls(SomeIpPayload):

    _include_struct_len = True

    Classn: Uint8

    ClassnQly: Uint8

    TrkInfo: Bool

    ObjDir: Uint8

    AbsDist: Float32

    VertAg: Float32

    HozlAg: Float32

    ObjHozlAgSpd: Float32

    ObjVertAgSpd: Float32

    DetdQly: Uint8

    ObjTimeStamp: Float64

    ObjId: Int16

    def __init__(self):

        self.Classn = Uint8()

        self.ClassnQly = Uint8()

        self.TrkInfo = Bool()

        self.ObjDir = Uint8()

        self.AbsDist = Float32()

        self.VertAg = Float32()

        self.HozlAg = Float32()

        self.ObjHozlAgSpd = Float32()

        self.ObjVertAgSpd = Float32()

        self.DetdQly = Uint8()

        self.ObjTimeStamp = Float64()

        self.ObjId = Int16()


class IdtNearestVehObj(SomeIpPayload):

    IdtNearestVehObj: IdtNearestVehObjKls

    def __init__(self):

        self.IdtNearestVehObj = IdtNearestVehObjKls()
