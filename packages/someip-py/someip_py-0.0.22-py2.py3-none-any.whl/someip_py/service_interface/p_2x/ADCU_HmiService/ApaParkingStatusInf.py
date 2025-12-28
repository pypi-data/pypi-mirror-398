from someip_py.codec import *


class IdtApaParkingStatusKls(SomeIpPayload):

    ViewSwitchReqSeN: Uint8

    ApaParkingOutStatusSeN: Uint8

    def __init__(self):

        self.ViewSwitchReqSeN = Uint8()

        self.ApaParkingOutStatusSeN = Uint8()


class IdtApaParkingStatus(SomeIpPayload):

    IdtApaParkingStatus: IdtApaParkingStatusKls

    def __init__(self):

        self.IdtApaParkingStatus = IdtApaParkingStatusKls()
