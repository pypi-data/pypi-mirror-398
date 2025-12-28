from someip_py.codec import *


class IdtWiprInfoKls(SomeIpPayload):

    _include_struct_len = True

    WipgSpdInfo: Uint8

    WiprActv: Uint8

    WiprInWipgAr: Uint8

    def __init__(self):

        self.WipgSpdInfo = Uint8()

        self.WiprActv = Uint8()

        self.WiprInWipgAr = Uint8()


class IdtWiprInfo(SomeIpPayload):

    IdtWiprInfo: IdtWiprInfoKls

    def __init__(self):

        self.IdtWiprInfo = IdtWiprInfoKls()
