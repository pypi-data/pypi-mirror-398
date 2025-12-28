from someip_py.codec import *


class IdtADPERCPProtoHeader(SomeIpPayload):

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


class IdtADPerceptionKls(SomeIpPayload):
    _has_dynamic_size = True

    ProtoHeader: IdtADPERCPProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtADPERCPProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtADPerception(SomeIpPayload):

    IdtADPerception: IdtADPerceptionKls

    def __init__(self):

        self.IdtADPerception = IdtADPerceptionKls()
