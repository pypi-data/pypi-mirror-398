from someip_py.codec import *


class IdtADHDMapProtoHeader(SomeIpPayload):

    _include_struct_len = True

    TimeStamp: Uint64

    TransId: Uint32

    Length: Uint32

    FieldId: Uint8

    ProtoVertion: Uint8

    Reserved: SomeIpFixedSizeArray[Uint8]

    def __init__(self):

        self.TimeStamp = Uint64()

        self.TransId = Uint32()

        self.Length = Uint32()

        self.FieldId = Uint8()

        self.ProtoVertion = Uint8()

        self.Reserved = SomeIpFixedSizeArray(Uint8, size=6, include_array_len=True)


class IdtADHDMapStsKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    ProtoHeader: IdtADHDMapProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtADHDMapProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtADHDMapSts(SomeIpPayload):

    IdtADHDMapSts: IdtADHDMapStsKls

    def __init__(self):

        self.IdtADHDMapSts = IdtADHDMapStsKls()
