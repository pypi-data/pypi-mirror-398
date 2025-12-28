from someip_py.codec import *


class IdtCameraIntInfRequest(SomeIpPayload):

    IdtCameraIntInfRequest: Uint8

    def __init__(self):

        self.IdtCameraIntInfRequest = Uint8()


class IdtCameraIntInfProtoHeader(SomeIpPayload):

    TimeStamp: Uint64

    TransId: Uint32

    Length: Uint32

    MessageId: Uint32

    ProtoVersion: Uint32

    Reserved: SomeIpFixedSizeArray[Uint8]

    def __init__(self):

        self.TimeStamp = Uint64()

        self.TransId = Uint32()

        self.Length = Uint32()

        self.MessageId = Uint32()

        self.ProtoVersion = Uint32()

        self.Reserved = SomeIpFixedSizeArray(Uint8, size=3)


class IdtCameraIntInfRetKls(SomeIpPayload):
    _has_dynamic_size = True

    ProtoHeader: IdtCameraIntInfProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtCameraIntInfProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtCameraIntInfRet(SomeIpPayload):

    IdtCameraIntInfRet: IdtCameraIntInfRetKls

    def __init__(self):

        self.IdtCameraIntInfRet = IdtCameraIntInfRetKls()
