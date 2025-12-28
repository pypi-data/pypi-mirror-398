from someip_py.codec import *


class IdtDMSInfoProtoHeader(SomeIpPayload):

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

        self.Reserved = SomeIpFixedSizeArray(Uint8, size=6)


class IdtDMSInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    ProtoHeader: IdtDMSInfoProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtDMSInfoProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtDMSInfo(SomeIpPayload):

    IdtDMSInfo: IdtDMSInfoKls

    def __init__(self):

        self.IdtDMSInfo = IdtDMSInfoKls()
