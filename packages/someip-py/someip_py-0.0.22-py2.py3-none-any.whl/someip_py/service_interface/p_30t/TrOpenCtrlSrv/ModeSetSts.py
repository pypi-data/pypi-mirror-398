from someip_py.codec import *


class IdtLinkageModSetStsKls(SomeIpPayload):

    _include_struct_len = True

    OnOff: Uint8

    def __init__(self):

        self.OnOff = Uint8()


class IdtLinkageModSetSts(SomeIpPayload):

    IdtLinkageModSetSts: IdtLinkageModSetStsKls

    def __init__(self):

        self.IdtLinkageModSetSts = IdtLinkageModSetStsKls()
