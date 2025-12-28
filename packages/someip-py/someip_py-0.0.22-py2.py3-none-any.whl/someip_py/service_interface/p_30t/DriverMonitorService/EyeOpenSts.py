from someip_py.codec import *


class IdtRiAndLeEyeOpenStsKls(SomeIpPayload):

    _include_struct_len = True

    EyeOpenStsLe: Uint8

    EyeOpenStsRi: Uint8

    def __init__(self):

        self.EyeOpenStsLe = Uint8()

        self.EyeOpenStsRi = Uint8()


class IdtRiAndLeEyeOpenSts(SomeIpPayload):

    IdtRiAndLeEyeOpenSts: IdtRiAndLeEyeOpenStsKls

    def __init__(self):

        self.IdtRiAndLeEyeOpenSts = IdtRiAndLeEyeOpenStsKls()
