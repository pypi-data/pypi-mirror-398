from someip_py.codec import *


class IdtRoadRoughIndcKls(SomeIpPayload):

    _include_struct_len = True

    RoadRoughType: Uint8

    RoadRoughDst: Float32

    def __init__(self):

        self.RoadRoughType = Uint8()

        self.RoadRoughDst = Float32()


class IdtRoadRoughIndc(SomeIpPayload):

    IdtRoadRoughIndc: IdtRoadRoughIndcKls

    def __init__(self):

        self.IdtRoadRoughIndc = IdtRoadRoughIndcKls()
