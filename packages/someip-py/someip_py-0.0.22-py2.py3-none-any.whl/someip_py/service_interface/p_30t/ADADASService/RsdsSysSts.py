from someip_py.codec import *


class IdtRsdsSysSts(SomeIpPayload):

    IdtRsdsSysSts: Uint8

    def __init__(self):

        self.IdtRsdsSysSts = Uint8()
