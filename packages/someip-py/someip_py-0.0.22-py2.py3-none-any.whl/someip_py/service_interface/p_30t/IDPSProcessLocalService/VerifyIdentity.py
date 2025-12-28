from someip_py.codec import *


class IdtZaidToken(SomeIpPayload):

    IdtZaidToken: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.IdtZaidToken = SomeIpDynamicSizeArray(Uint8)


class IdtVerifyIdentityResultKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    VerifyReturnCode: Uint8

    MethodIdList: SomeIpDynamicSizeArray[Uint16]

    TopicIdList: SomeIpDynamicSizeArray[Uint16]

    def __init__(self):

        self.VerifyReturnCode = Uint8()

        self.MethodIdList = SomeIpDynamicSizeArray(Uint16)

        self.TopicIdList = SomeIpDynamicSizeArray(Uint16)


class IdtVerifyIdentityResult(SomeIpPayload):

    IdtVerifyIdentityResult: IdtVerifyIdentityResultKls

    def __init__(self):

        self.IdtVerifyIdentityResult = IdtVerifyIdentityResultKls()
