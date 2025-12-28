from someip_py.codec import *


class IdtPrkAssiAudWarnKls(SomeIpPayload):

    _include_struct_len = True

    PrkAssiAudWarnRe: Uint8

    PrkAssiAudWarnFrnt: Uint8

    def __init__(self):

        self.PrkAssiAudWarnRe = Uint8()

        self.PrkAssiAudWarnFrnt = Uint8()


class IdtPrkAssiAudWarn(SomeIpPayload):

    IdtPrkAssiAudWarn: IdtPrkAssiAudWarnKls

    def __init__(self):

        self.IdtPrkAssiAudWarn = IdtPrkAssiAudWarnKls()
