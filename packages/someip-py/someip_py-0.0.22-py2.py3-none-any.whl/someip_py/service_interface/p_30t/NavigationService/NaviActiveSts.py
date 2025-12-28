from someip_py.codec import *


class IdtActiveSts(SomeIpPayload):

    IdtActiveSts: Bool

    def __init__(self):

        self.IdtActiveSts = Bool()
