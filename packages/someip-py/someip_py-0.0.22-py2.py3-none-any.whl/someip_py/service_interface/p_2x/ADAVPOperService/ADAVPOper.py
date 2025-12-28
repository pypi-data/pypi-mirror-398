from someip_py.codec import *


class IdtADAVPOperProtoHeader(SomeIpPayload):

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


class IdtADAVPOperRequestKls(SomeIpPayload):
    _has_dynamic_size = True

    ProtoHeader: IdtADAVPOperProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtADAVPOperProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtADAVPOperRequest(SomeIpPayload):

    IdtADAVPOperRequest: IdtADAVPOperRequestKls

    def __init__(self):

        self.IdtADAVPOperRequest = IdtADAVPOperRequestKls()


class IdtADAVPOperRet(SomeIpPayload):

    IdtADAVPOperRet: Uint8

    def __init__(self):

        self.IdtADAVPOperRet = Uint8()
