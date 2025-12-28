from someip_py.codec import *


class IdtExLiMode3Sts(SomeIpPayload):

    IdtExLiMode3Sts: Uint8

    def __init__(self):

        self.IdtExLiMode3Sts = Uint8()
