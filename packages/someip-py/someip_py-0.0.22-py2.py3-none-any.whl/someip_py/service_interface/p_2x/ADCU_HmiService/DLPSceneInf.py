from someip_py.codec import *


class IdtDLPSceneKls(SomeIpPayload):

    SceneEnterExitSeN: Uint8

    SceneTypeSeN: Uint8

    PositionInfoSeN: Uint8

    DistanceSeN: Uint32

    def __init__(self):

        self.SceneEnterExitSeN = Uint8()

        self.SceneTypeSeN = Uint8()

        self.PositionInfoSeN = Uint8()

        self.DistanceSeN = Uint32()


class IdtDLPScene(SomeIpPayload):

    IdtDLPScene: IdtDLPSceneKls

    def __init__(self):

        self.IdtDLPScene = IdtDLPSceneKls()
