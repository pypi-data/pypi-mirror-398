from someip_py.codec import *


class IdtBLEKeyButtonSts2Kls(SomeIpPayload):

    _include_struct_len = True

    BLEKeyButtonSts2Action: Uint8

    BLEKeyButtonSts2ID: Uint8

    BLEKeyButtonSts2NO: Uint8

    def __init__(self):

        self.BLEKeyButtonSts2Action = Uint8()

        self.BLEKeyButtonSts2ID = Uint8()

        self.BLEKeyButtonSts2NO = Uint8()


class IdtBLEKeyButtonSts2(SomeIpPayload):

    IdtBLEKeyButtonSts2: IdtBLEKeyButtonSts2Kls

    def __init__(self):

        self.IdtBLEKeyButtonSts2 = IdtBLEKeyButtonSts2Kls()


class IdtBLEKeyButtonRet(SomeIpPayload):

    IdtBLEKeyButtonRet: Uint8

    def __init__(self):

        self.IdtBLEKeyButtonRet = Uint8()
