from someip_py.codec import *


class ApaSlelectedSlotParkingmodeKls(SomeIpPayload):

    ApaSlelectedSlotParkingmodeSeN: Uint8

    def __init__(self):

        self.ApaSlelectedSlotParkingmodeSeN = Uint8()


class ApaSlelectedSlotParkingmode(SomeIpPayload):

    ApaSlelectedSlotParkingmode: ApaSlelectedSlotParkingmodeKls

    def __init__(self):

        self.ApaSlelectedSlotParkingmode = ApaSlelectedSlotParkingmodeKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
