from someip_py.codec import *


class IdtParkingInteractiveStatusKls(SomeIpPayload):

    PrkgInterStsSeN: Uint8

    PrkgInterIDSeN: Uint32

    PrkgStationIDSeN: Uint32

    def __init__(self):

        self.PrkgInterStsSeN = Uint8()

        self.PrkgInterIDSeN = Uint32()

        self.PrkgStationIDSeN = Uint32()


class IdtParkingInteractiveStatus(SomeIpPayload):

    IdtParkingInteractiveStatus: IdtParkingInteractiveStatusKls

    def __init__(self):

        self.IdtParkingInteractiveStatus = IdtParkingInteractiveStatusKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
