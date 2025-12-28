from someip_py.codec import *


class IdtSingleDoorAvailability(SomeIpPayload):

    _include_struct_len = True

    DoorID: Uint8

    DoorAvailability: Uint8

    def __init__(self):

        self.DoorID = Uint8()

        self.DoorAvailability = Uint8()


class IdtDoorsAvailability(SomeIpPayload):

    IdtDoorsAvailability: SomeIpDynamicSizeArray[IdtSingleDoorAvailability]

    def __init__(self):

        self.IdtDoorsAvailability = SomeIpDynamicSizeArray(IdtSingleDoorAvailability)
