from someip_py.codec import *


class IdtParkingInteractiveKls(SomeIpPayload):

    PrkgInteractiveSeN: Uint8

    PrkgInterIDSeN: Uint32

    PrkgStationIDSeN: Uint32

    def __init__(self):

        self.PrkgInteractiveSeN = Uint8()

        self.PrkgInterIDSeN = Uint32()

        self.PrkgStationIDSeN = Uint32()


class IdtParkingInteractive(SomeIpPayload):

    IdtParkingInteractive: IdtParkingInteractiveKls

    def __init__(self):

        self.IdtParkingInteractive = IdtParkingInteractiveKls()
