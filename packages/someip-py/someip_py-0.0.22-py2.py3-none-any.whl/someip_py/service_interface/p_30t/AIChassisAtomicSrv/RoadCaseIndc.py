from someip_py.codec import *


class IdtRoadCaseIndcKls(SomeIpPayload):

    _include_struct_len = True

    RoadCase: Uint8

    RoadCaseDst: Float32

    def __init__(self):

        self.RoadCase = Uint8()

        self.RoadCaseDst = Float32()


class IdtRoadCaseIndc(SomeIpPayload):

    IdtRoadCaseIndc: IdtRoadCaseIndcKls

    def __init__(self):

        self.IdtRoadCaseIndc = IdtRoadCaseIndcKls()
