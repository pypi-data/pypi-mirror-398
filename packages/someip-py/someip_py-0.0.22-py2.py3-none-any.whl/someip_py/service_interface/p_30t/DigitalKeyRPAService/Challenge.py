from someip_py.codec import *


class IdtRpaChallengeReqKls(SomeIpPayload):

    _include_struct_len = True

    RndX: Uint8

    RndY: Uint8

    AuthentSts: Uint8

    def __init__(self):

        self.RndX = Uint8()

        self.RndY = Uint8()

        self.AuthentSts = Uint8()


class IdtRpaChallengeReq(SomeIpPayload):

    IdtRpaChallengeReq: IdtRpaChallengeReqKls

    def __init__(self):

        self.IdtRpaChallengeReq = IdtRpaChallengeReqKls()


class IdtRpaReturnCode(SomeIpPayload):

    IdtRpaReturnCode: Uint8

    def __init__(self):

        self.IdtRpaReturnCode = Uint8()
