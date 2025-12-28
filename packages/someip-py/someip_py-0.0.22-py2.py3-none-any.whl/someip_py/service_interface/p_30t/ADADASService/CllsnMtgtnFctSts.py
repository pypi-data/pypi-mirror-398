from someip_py.codec import *


class IdtCllsnMtgtnFctSts(SomeIpPayload):

    IdtCllsnMtgtnFctSts: Uint8

    def __init__(self):

        self.IdtCllsnMtgtnFctSts = Uint8()
