from someip_py.codec import *


class NOPTime1(SomeIpPayload):

    hour: Uint16

    minute: Uint16

    def __init__(self):

        self.hour = Uint16()

        self.minute = Uint16()


class LCCDataUploadInfoKls(SomeIpPayload):

    LCCTimeSeN: NOPTime1

    LCCDistanceSeN: Uint16

    def __init__(self):

        self.LCCTimeSeN = NOPTime1()

        self.LCCDistanceSeN = Uint16()


class LCCDataUploadInfo(SomeIpPayload):

    LCCDataUploadInfo: LCCDataUploadInfoKls

    def __init__(self):

        self.LCCDataUploadInfo = LCCDataUploadInfoKls()
