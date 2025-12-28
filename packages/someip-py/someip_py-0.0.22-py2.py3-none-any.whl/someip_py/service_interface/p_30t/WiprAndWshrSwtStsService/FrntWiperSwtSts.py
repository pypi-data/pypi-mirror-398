from someip_py.codec import *


class IdtFrntWiprKls(SomeIpPayload):

    _include_struct_len = True

    FrntWiprLvrCmd: Uint8

    FrntWiprLvrQf: Uint8

    def __init__(self):

        self.FrntWiprLvrCmd = Uint8()

        self.FrntWiprLvrQf = Uint8()


class IdtFrntWipr(SomeIpPayload):

    IdtFrntWipr: IdtFrntWiprKls

    def __init__(self):

        self.IdtFrntWipr = IdtFrntWiprKls()
