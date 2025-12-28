from someip_py.codec import *


class IdtWadDepthDetSysKls(SomeIpPayload):

    _include_struct_len = True

    WadDepth: Uint8

    WadDepthLftSnsFltSts: Uint8

    WadDepthRiSnsFltSts: Uint8

    WadDepthDetSts: Uint8

    def __init__(self):

        self.WadDepth = Uint8()

        self.WadDepthLftSnsFltSts = Uint8()

        self.WadDepthRiSnsFltSts = Uint8()

        self.WadDepthDetSts = Uint8()


class IdtWadDepthDetSys(SomeIpPayload):

    IdtWadDepthDetSys: IdtWadDepthDetSysKls

    def __init__(self):

        self.IdtWadDepthDetSys = IdtWadDepthDetSysKls()
