from someip_py.codec import *


class IdtDstEstimdToEmptyValue(SomeIpPayload):

    IdtDstEstimdToEmptyValue: Uint16

    def __init__(self):

        self.IdtDstEstimdToEmptyValue = Uint16()
