from someip_py.codec import *


class IdtSuspAdjCount(SomeIpPayload):

    IdtSuspAdjCount: Int16

    def __init__(self):

        self.IdtSuspAdjCount = Int16()
