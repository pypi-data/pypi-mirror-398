from someip_py.codec import *


class IdtExtLiSwitchSts3(SomeIpPayload):

    IdtExtLiSwitchSts3: Uint8

    def __init__(self):

        self.IdtExtLiSwitchSts3 = Uint8()
