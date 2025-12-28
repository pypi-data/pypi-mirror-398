from someip_py.codec import *


class IdtCDCModeEnaStsStruKls(SomeIpPayload):

    _include_struct_len = True

    Comfort: Uint8

    Normal: Uint8

    Sport: Uint8

    SportPlus: Uint8

    def __init__(self):

        self.Comfort = Uint8()

        self.Normal = Uint8()

        self.Sport = Uint8()

        self.SportPlus = Uint8()


class IdtCDCModeEnaStsStru(SomeIpPayload):

    IdtCDCModeEnaStsStru: IdtCDCModeEnaStsStruKls

    def __init__(self):

        self.IdtCDCModeEnaStsStru = IdtCDCModeEnaStsStruKls()
