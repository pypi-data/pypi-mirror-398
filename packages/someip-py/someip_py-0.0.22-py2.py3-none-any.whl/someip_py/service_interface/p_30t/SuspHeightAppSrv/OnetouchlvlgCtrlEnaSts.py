from someip_py.codec import *


class IdtOnetouchlvlgCtrlEnaSts(SomeIpPayload):

    IdtOnetouchlvlgCtrlEnaSts: Uint8

    def __init__(self):

        self.IdtOnetouchlvlgCtrlEnaSts = Uint8()
