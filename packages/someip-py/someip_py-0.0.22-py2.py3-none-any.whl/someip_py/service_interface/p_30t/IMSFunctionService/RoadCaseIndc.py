from someip_py.codec import *


class IdtRoadCaseIndctKls(SomeIpPayload):

    _include_struct_len = True

    RoadCase: Uint8

    RoadCaseDst: Float32

    def __init__(self):

        self.RoadCase = Uint8()

        self.RoadCaseDst = Float32()


class IdtRoadCaseIndct(SomeIpPayload):

    IdtRoadCaseIndct: IdtRoadCaseIndctKls

    def __init__(self):

        self.IdtRoadCaseIndct = IdtRoadCaseIndctKls()
