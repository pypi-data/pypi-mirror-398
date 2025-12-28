from someip_py.codec import *


class IdtASMPwrSavingMod(SomeIpPayload):

    IdtASMPwrSavingMod: Uint8

    def __init__(self):

        self.IdtASMPwrSavingMod = Uint8()


class IdtASMPwrSavingReqSrc(SomeIpPayload):

    IdtASMPwrSavingReqSrc: Uint8

    def __init__(self):

        self.IdtASMPwrSavingReqSrc = Uint8()


class IdtASMPwrSavingReqRes(SomeIpPayload):

    IdtASMPwrSavingReqRes: Uint8

    def __init__(self):

        self.IdtASMPwrSavingReqRes = Uint8()
