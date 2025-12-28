from someip_py.codec import *


class IdtSubmersionAlrmStsKls(SomeIpPayload):

    _include_struct_len = True

    SubmersionAlrmOnOffSts: Uint8

    SubmersionModReq: Uint8

    def __init__(self):

        self.SubmersionAlrmOnOffSts = Uint8()

        self.SubmersionModReq = Uint8()


class IdtSubmersionAlrmSts(SomeIpPayload):

    IdtSubmersionAlrmSts: IdtSubmersionAlrmStsKls

    def __init__(self):

        self.IdtSubmersionAlrmSts = IdtSubmersionAlrmStsKls()
