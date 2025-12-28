from someip_py.codec import *


class IdtRpaAnswerKls(SomeIpPayload):

    _include_struct_len = True

    RndXAnswer: Uint8

    RndYAnswer: Uint8

    AnswerResp: Uint16

    phoneStatus: Uint8

    CMAC: Uint64

    def __init__(self):

        self.RndXAnswer = Uint8()

        self.RndYAnswer = Uint8()

        self.AnswerResp = Uint16()

        self.phoneStatus = Uint8()

        self.CMAC = Uint64()


class IdtRpaAnswer(SomeIpPayload):

    IdtRpaAnswer: IdtRpaAnswerKls

    def __init__(self):

        self.IdtRpaAnswer = IdtRpaAnswerKls()
