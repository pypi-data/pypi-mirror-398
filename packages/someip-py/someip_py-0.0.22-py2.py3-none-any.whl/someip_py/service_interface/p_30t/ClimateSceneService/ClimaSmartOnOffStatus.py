from someip_py.codec import *


class IdtClimaSmartStsKls(SomeIpPayload):

    _include_struct_len = True

    PassSmtSts: Uint8

    SecSmtSts: Uint8

    ThrdSmtSts: Uint8

    def __init__(self):

        self.PassSmtSts = Uint8()

        self.SecSmtSts = Uint8()

        self.ThrdSmtSts = Uint8()


class IdtClimaSmartSts(SomeIpPayload):

    IdtClimaSmartSts: IdtClimaSmartStsKls

    def __init__(self):

        self.IdtClimaSmartSts = IdtClimaSmartStsKls()
