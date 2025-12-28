from someip_py.codec import *


class IdtVin(SomeIpPayload):

    IdtVin: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtVin = SomeIpDynamicSizeString()
