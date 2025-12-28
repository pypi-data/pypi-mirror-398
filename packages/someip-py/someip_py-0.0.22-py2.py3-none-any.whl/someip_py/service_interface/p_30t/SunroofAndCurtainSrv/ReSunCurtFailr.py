from someip_py.codec import *


class IdtSunCurtFailrKls(SomeIpPayload):

    _include_struct_len = True

    CurtMotNotAvl: Uint8

    CurtMotFailr: Uint8

    CurtMotMotHallNotAvl: Uint8

    CurtMotHallFailr: Uint8

    def __init__(self):

        self.CurtMotNotAvl = Uint8()

        self.CurtMotFailr = Uint8()

        self.CurtMotMotHallNotAvl = Uint8()

        self.CurtMotHallFailr = Uint8()


class IdtSunCurtFailr(SomeIpPayload):

    IdtSunCurtFailr: IdtSunCurtFailrKls

    def __init__(self):

        self.IdtSunCurtFailr = IdtSunCurtFailrKls()
