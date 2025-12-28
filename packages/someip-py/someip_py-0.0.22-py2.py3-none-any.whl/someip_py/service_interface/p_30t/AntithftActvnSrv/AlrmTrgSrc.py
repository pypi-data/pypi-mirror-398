from someip_py.codec import *


class IdtAlrmTrgSrc(SomeIpPayload):

    IdtAlrmTrgSrc: Uint8

    def __init__(self):

        self.IdtAlrmTrgSrc = Uint8()
