from someip_py.codec import *


class IdtDstEstimdToEmptyDispMode(SomeIpPayload):

    IdtDstEstimdToEmptyDispMode: Uint8

    def __init__(self):

        self.IdtDstEstimdToEmptyDispMode = Uint8()
