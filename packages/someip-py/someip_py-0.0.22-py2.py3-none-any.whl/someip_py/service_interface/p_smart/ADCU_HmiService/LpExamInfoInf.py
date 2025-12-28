from someip_py.codec import *


class LpExamInfoKls(SomeIpPayload):

    LpExamSeN: Uint8

    def __init__(self):

        self.LpExamSeN = Uint8()


class LpExamInfo(SomeIpPayload):

    LpExamInfo: LpExamInfoKls

    def __init__(self):

        self.LpExamInfo = LpExamInfoKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
