from someip_py.codec import *


class IdtParkingAPAKls(SomeIpPayload):
    _has_dynamic_size = True

    ApaZekSlotSeN: Uint8

    ApaZekSlotNumSeN: SomeIpDynamicSizeArray[Int8]

    ApaZekSlotLockStsSeN: Uint8

    MRSelectSlotID: Uint32

    def __init__(self):

        self.ApaZekSlotSeN = Uint8()

        self.ApaZekSlotNumSeN = SomeIpDynamicSizeArray(Int8)

        self.ApaZekSlotLockStsSeN = Uint8()

        self.MRSelectSlotID = Uint32()


class IdtParkingAPA(SomeIpPayload):

    IdtParkingAPA: IdtParkingAPAKls

    def __init__(self):

        self.IdtParkingAPA = IdtParkingAPAKls()
