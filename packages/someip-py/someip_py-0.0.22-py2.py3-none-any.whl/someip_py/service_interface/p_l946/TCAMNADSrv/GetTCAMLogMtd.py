from someip_py.codec import *


class GetLogRespStructKls(SomeIpPayload):

    _include_struct_len = True

    GetLogResponse: Uint8

    RetVal: Uint8

    def __init__(self):

        self.GetLogResponse = Uint8()

        self.RetVal = Uint8()


class GetLogRespStruct(SomeIpPayload):

    GetLogRespStruct: GetLogRespStructKls

    def __init__(self):

        self.GetLogRespStruct = GetLogRespStructKls()
