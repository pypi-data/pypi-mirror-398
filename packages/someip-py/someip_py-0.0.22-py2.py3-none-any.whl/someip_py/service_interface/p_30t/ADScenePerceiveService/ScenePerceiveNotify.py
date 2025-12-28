from someip_py.codec import *


class IdtScenePerceiveStsKls(SomeIpPayload):

    _include_struct_len = True

    SceneEnterExit: Uint8

    SceneType: Uint8

    PositionInfo: Uint16

    Distance: Uint32

    ReservedPara: SomeIpFixedSizeArray[Uint16]

    def __init__(self):

        self.SceneEnterExit = Uint8()

        self.SceneType = Uint8()

        self.PositionInfo = Uint16()

        self.Distance = Uint32()

        self.ReservedPara = SomeIpFixedSizeArray(
            Uint16, size=20, include_array_len=True
        )


class IdtScenePerceiveSts(SomeIpPayload):

    IdtScenePerceiveSts: IdtScenePerceiveStsKls

    def __init__(self):

        self.IdtScenePerceiveSts = IdtScenePerceiveStsKls()
