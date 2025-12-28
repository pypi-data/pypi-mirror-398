from someip_py.codec import *


class IdtSunRoofFailrKls(SomeIpPayload):

    _include_struct_len = True

    EcuFailrGen: Uint8

    RoofMotNotAvl: Uint8

    RoofMotFailr: Uint8

    RoofMotHalltFailr: Uint8

    def __init__(self):

        self.EcuFailrGen = Uint8()

        self.RoofMotNotAvl = Uint8()

        self.RoofMotFailr = Uint8()

        self.RoofMotHalltFailr = Uint8()


class IdtSunRoofFailr(SomeIpPayload):

    IdtSunRoofFailr: IdtSunRoofFailrKls

    def __init__(self):

        self.IdtSunRoofFailr = IdtSunRoofFailrKls()
