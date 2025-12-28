from someip_py.codec import *


class IdtAVPCollectedDestinationCmdKls(SomeIpPayload):

    CollectedDestinationType: Uint8

    CollectedDestinationSlotId: Uint32

    def __init__(self):

        self.CollectedDestinationType = Uint8()

        self.CollectedDestinationSlotId = Uint32()


class IdtAVPCollectedDestinationCmd(SomeIpPayload):

    IdtAVPCollectedDestinationCmd: IdtAVPCollectedDestinationCmdKls

    def __init__(self):

        self.IdtAVPCollectedDestinationCmd = IdtAVPCollectedDestinationCmdKls()
