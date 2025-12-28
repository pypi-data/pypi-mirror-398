from someip_py.codec import *


class IdtPwrLvlEleKls(SomeIpPayload):

    _include_struct_len = True

    PwrLvlEleMai: Uint8

    PwrLvlEleSubtyp: Uint8

    def __init__(self):

        self.PwrLvlEleMai = Uint8()

        self.PwrLvlEleSubtyp = Uint8()


class IdtPwrLvlEle(SomeIpPayload):

    IdtPwrLvlEle: IdtPwrLvlEleKls

    def __init__(self):

        self.IdtPwrLvlEle = IdtPwrLvlEleKls()
