from someip_py.codec import *


class IdtADDrivingRequestKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    Code: Uint8

    Para: SomeIpDynamicSizeArray[Int32]

    def __init__(self):

        self.Code = Uint8()

        self.Para = SomeIpDynamicSizeArray(Int32)


class IdtADDrivingRequest(SomeIpPayload):

    IdtADDrivingRequest: IdtADDrivingRequestKls

    def __init__(self):

        self.IdtADDrivingRequest = IdtADDrivingRequestKls()


class IdtADDrivingRet(SomeIpPayload):

    IdtADDrivingRet: Uint8

    def __init__(self):

        self.IdtADDrivingRet = Uint8()
