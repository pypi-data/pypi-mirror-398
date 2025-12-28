from someip_py.codec import *


class IdtRoadTypeRecgKls(SomeIpPayload):

    _include_struct_len = True

    RoadTypeRecgInf: Uint8

    RoadTypeRecgSts: Uint8

    RoadTypeRecgConfidence: Uint8

    def __init__(self):

        self.RoadTypeRecgInf = Uint8()

        self.RoadTypeRecgSts = Uint8()

        self.RoadTypeRecgConfidence = Uint8()


class IdtRoadTypeRecg(SomeIpPayload):

    IdtRoadTypeRecg: IdtRoadTypeRecgKls

    def __init__(self):

        self.IdtRoadTypeRecg = IdtRoadTypeRecgKls()
