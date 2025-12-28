from someip_py.codec import *


class IdtTimeToDestinationKls(SomeIpPayload):

    _include_struct_len = True

    NaviDay: Uint8

    NaviHour: Uint8

    NaviMinutes: Uint8

    def __init__(self):

        self.NaviDay = Uint8()

        self.NaviHour = Uint8()

        self.NaviMinutes = Uint8()


class IdtTimeToDestination(SomeIpPayload):

    IdtTimeToDestination: IdtTimeToDestinationKls

    def __init__(self):

        self.IdtTimeToDestination = IdtTimeToDestinationKls()
