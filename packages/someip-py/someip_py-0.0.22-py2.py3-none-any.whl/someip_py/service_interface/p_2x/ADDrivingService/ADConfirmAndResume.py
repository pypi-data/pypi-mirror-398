from someip_py.codec import *


class IdtADConfirmAndResume(SomeIpPayload):

    IdtADConfirmAndResume: Uint8

    def __init__(self):

        self.IdtADConfirmAndResume = Uint8()


class IdtADConfirmAndResumeRet(SomeIpPayload):

    IdtADConfirmAndResumeRet: Uint8

    def __init__(self):

        self.IdtADConfirmAndResumeRet = Uint8()
