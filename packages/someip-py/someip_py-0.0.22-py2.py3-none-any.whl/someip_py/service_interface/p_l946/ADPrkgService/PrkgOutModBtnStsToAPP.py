from someip_py.codec import *


class IdtPrkgOutModBtnStsToAPP2Kls(SomeIpPayload):

    _include_struct_len = True

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts1: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts2: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts3: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts4: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts5: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts6: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts7: Uint8

    PrkgOutModBtnStsToAPPPrkgOutModBtnSts8: Uint8

    def __init__(self):

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts1 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts2 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts3 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts4 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts5 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts6 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts7 = Uint8()

        self.PrkgOutModBtnStsToAPPPrkgOutModBtnSts8 = Uint8()


class IdtPrkgOutModBtnStsToAPP2(SomeIpPayload):

    IdtPrkgOutModBtnStsToAPP2: IdtPrkgOutModBtnStsToAPP2Kls

    def __init__(self):

        self.IdtPrkgOutModBtnStsToAPP2 = IdtPrkgOutModBtnStsToAPP2Kls()
