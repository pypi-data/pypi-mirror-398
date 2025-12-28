from someip_py.codec import *


class Progress(SomeIpPayload):

    Progress: Int8

    def __init__(self):

        self.Progress = Int8()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
