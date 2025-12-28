from someip_py.codec import *


class IdtAVMCameraProtoHeader(SomeIpPayload):

    _include_struct_len = True

    TimeStamp: Uint64

    TransId: Uint32

    Length: Uint32

    FieldId: Uint8

    ProtoVersion: Uint8

    Reserved: SomeIpFixedSizeArray[Uint8]

    def __init__(self):

        self.TimeStamp = Uint64()

        self.TransId = Uint32()

        self.Length = Uint32()

        self.FieldId = Uint8()

        self.ProtoVersion = Uint8()

        self.Reserved = SomeIpFixedSizeArray(Uint8, size=6)


class IdtAVMCameraKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    ProtoHeader: IdtAVMCameraProtoHeader

    ProtoPayload: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.ProtoHeader = IdtAVMCameraProtoHeader()

        self.ProtoPayload = SomeIpDynamicSizeArray(Uint8)


class IdtAVMCamera(SomeIpPayload):

    IdtAVMCamera: IdtAVMCameraKls

    def __init__(self):

        self.IdtAVMCamera = IdtAVMCameraKls()
