from someip_py.codec import *


class IdtEgyLvlEleKls(SomeIpPayload):

    _include_struct_len = True

    EgyLvlEleMai: Uint8

    EgyLvlEleSubtyp: Uint8

    def __init__(self):

        self.EgyLvlEleMai = Uint8()

        self.EgyLvlEleSubtyp = Uint8()


class IdtEgyLvlEle(SomeIpPayload):

    IdtEgyLvlEle: IdtEgyLvlEleKls

    def __init__(self):

        self.IdtEgyLvlEle = IdtEgyLvlEleKls()
