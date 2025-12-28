from someip_py.codec import *


class FunctionListType(SomeIpPayload):

    ZidKey: Uint8

    ZidValue: Uint8

    def __init__(self):

        self.ZidKey = Uint8()

        self.ZidValue = Uint8()


class IdtZidForbidKls(SomeIpPayload):
    _has_dynamic_size = True

    ZIDForbidSeN: SomeIpDynamicSizeArray[FunctionListType]

    def __init__(self):

        self.ZIDForbidSeN = SomeIpDynamicSizeArray(FunctionListType)


class IdtZidForbid(SomeIpPayload):

    IdtZidForbid: IdtZidForbidKls

    def __init__(self):

        self.IdtZidForbid = IdtZidForbidKls()
