from someip_py.codec import *


class IdtCCLPartNumber(SomeIpPayload):

    IdtCCLPartNumber: SomeIpFixedSizeArray[Uint8]

    def __init__(self):

        self.IdtCCLPartNumber = SomeIpFixedSizeArray(
            Uint8, size=8, include_array_len=True
        )
