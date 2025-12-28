from someip_py.codec import *


class IdtCommonObj(SomeIpPayload):

    _include_struct_len = True

    AbsDist: Float32

    CommonObjType: Uint8

    Classn: Uint8

    ClassnQly: Uint8

    HozlAgLe: Float32

    HozlAgRi: Float32

    ObjDir: Uint8

    ObjHozlAgSpdLe: Float32

    ObjHozlAgSpdRi: Float32

    TrkInfo: Bool

    VertAgBot: Float32

    VertAgTop: Float32

    ObjTimeStamp: Uint64

    ObjId: Uint16

    def __init__(self):

        self.AbsDist = Float32()

        self.CommonObjType = Uint8()

        self.Classn = Uint8()

        self.ClassnQly = Uint8()

        self.HozlAgLe = Float32()

        self.HozlAgRi = Float32()

        self.ObjDir = Uint8()

        self.ObjHozlAgSpdLe = Float32()

        self.ObjHozlAgSpdRi = Float32()

        self.TrkInfo = Bool()

        self.VertAgBot = Float32()

        self.VertAgTop = Float32()

        self.ObjTimeStamp = Uint64()

        self.ObjId = Uint16()


class IdtPerceptionObjsADBKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    PerceptionQly: Uint8

    HostVehInLitArea: Bool

    PercepObjsADB: SomeIpDynamicSizeArray[IdtCommonObj]

    def __init__(self):

        self.PerceptionQly = Uint8()

        self.HostVehInLitArea = Bool()

        self.PercepObjsADB = SomeIpDynamicSizeArray(IdtCommonObj)


class IdtPerceptionObjsADB(SomeIpPayload):

    IdtPerceptionObjsADB: IdtPerceptionObjsADBKls

    def __init__(self):

        self.IdtPerceptionObjsADB = IdtPerceptionObjsADBKls()
