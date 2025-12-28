from someip_py.codec import *


class NaviDataInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    NaviDataTypeSeN: Uint8

    NaviDataInfoSeN: SomeIpDynamicSizeArray[Uint8]

    def __init__(self):

        self.NaviDataTypeSeN = Uint8()

        self.NaviDataInfoSeN = SomeIpDynamicSizeArray(Uint8)


class NaviDataInfo(SomeIpPayload):

    NaviDataInfo: NaviDataInfoKls

    def __init__(self):

        self.NaviDataInfo = NaviDataInfoKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
