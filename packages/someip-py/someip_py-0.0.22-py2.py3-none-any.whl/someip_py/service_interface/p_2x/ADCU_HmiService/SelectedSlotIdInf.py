from someip_py.codec import *


class IdtSelectedSlotIdKls(SomeIpPayload):

    ID32bit: Uint32

    DriverSelectNotAvailableSlotIDSeN: Uint32

    ApaSlelectedDirectionSeN: Uint8

    def __init__(self):

        self.ID32bit = Uint32()

        self.DriverSelectNotAvailableSlotIDSeN = Uint32()

        self.ApaSlelectedDirectionSeN = Uint8()


class IdtSelectedSlotId(SomeIpPayload):

    IdtSelectedSlotId: IdtSelectedSlotIdKls

    def __init__(self):

        self.IdtSelectedSlotId = IdtSelectedSlotIdKls()
