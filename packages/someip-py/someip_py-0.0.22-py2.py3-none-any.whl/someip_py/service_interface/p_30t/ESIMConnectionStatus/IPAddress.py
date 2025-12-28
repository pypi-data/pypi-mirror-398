from someip_py.codec import *


class IdtSimIPAdr(SomeIpPayload):

    _include_struct_len = True

    SimNo: Uint8

    SimIPAdr: SomeIpDynamicSizeString

    def __init__(self):

        self.SimNo = Uint8()

        self.SimIPAdr = SomeIpDynamicSizeString()


class IdtAllIPAdr(SomeIpPayload):

    IdtAllIPAdr: SomeIpDynamicSizeArray[IdtSimIPAdr]

    def __init__(self):

        self.IdtAllIPAdr = SomeIpDynamicSizeArray(IdtSimIPAdr)
