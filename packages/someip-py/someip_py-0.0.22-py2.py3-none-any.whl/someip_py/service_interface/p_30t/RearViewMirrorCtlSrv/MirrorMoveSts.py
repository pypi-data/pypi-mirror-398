from someip_py.codec import *


class IdtMirrorMoveSts(SomeIpPayload):

    _include_struct_len = True

    MirrMoveSts: Uint8

    MirrMoveScenario: Uint8

    def __init__(self):

        self.MirrMoveSts = Uint8()

        self.MirrMoveScenario = Uint8()


class IdtBothMirrorMoveSts(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrorMoveSts: IdtMirrorMoveSts

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrorMoveSts = IdtMirrorMoveSts()


class IdtMirrorMoveStsAry(SomeIpPayload):

    IdtMirrorMoveStsAry: SomeIpDynamicSizeArray[IdtBothMirrorMoveSts]

    def __init__(self):

        self.IdtMirrorMoveStsAry = SomeIpDynamicSizeArray(IdtBothMirrorMoveSts)
