from someip_py.codec import *


class IdtMirrorPositionSts(SomeIpPayload):

    _include_struct_len = True

    Xposition: Uint16

    Yposition: Uint16

    def __init__(self):

        self.Xposition = Uint16()

        self.Yposition = Uint16()


class IdtBothMirrDwnPosition(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrorPositionSts: IdtMirrorPositionSts

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrorPositionSts = IdtMirrorPositionSts()


class IdtMirrDwnPositionSetAry(SomeIpPayload):

    IdtMirrDwnPositionSetAry: SomeIpDynamicSizeArray[IdtBothMirrDwnPosition]

    def __init__(self):

        self.IdtMirrDwnPositionSetAry = SomeIpDynamicSizeArray(IdtBothMirrDwnPosition)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
