from someip_py.codec import *


class MapButtonCmdType(SomeIpPayload):

    MapButtonCmdType: Uint8

    def __init__(self):

        self.MapButtonCmdType = Uint8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
