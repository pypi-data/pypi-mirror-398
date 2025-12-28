from someip_py.codec import *


class IdtOneClickStsKls(SomeIpPayload):

    _include_struct_len = True

    OnOff: Uint8

    def __init__(self):

        self.OnOff = Uint8()


class IdtOneClickSts(SomeIpPayload):

    IdtOneClickSts: IdtOneClickStsKls

    def __init__(self):

        self.IdtOneClickSts = IdtOneClickStsKls()
