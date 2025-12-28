from someip_py.codec import *


class IdtADUOSelectedSlotId(SomeIpPayload):

    IdtADUOSelectedSlotId: Uint32

    def __init__(self):

        self.IdtADUOSelectedSlotId = Uint32()


class IdtADUORet(SomeIpPayload):

    IdtADUORet: Uint8

    def __init__(self):

        self.IdtADUORet = Uint8()
