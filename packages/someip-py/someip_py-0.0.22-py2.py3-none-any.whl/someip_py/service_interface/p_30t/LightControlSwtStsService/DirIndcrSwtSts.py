from someip_py.codec import *


class IdtSwtDirIndcrKls(SomeIpPayload):

    _include_struct_len = True

    SwtDirIndcrSts: Uint8

    SwtQf: Uint8

    def __init__(self):

        self.SwtDirIndcrSts = Uint8()

        self.SwtQf = Uint8()


class IdtSwtDirIndcr(SomeIpPayload):

    IdtSwtDirIndcr: IdtSwtDirIndcrKls

    def __init__(self):

        self.IdtSwtDirIndcr = IdtSwtDirIndcrKls()
