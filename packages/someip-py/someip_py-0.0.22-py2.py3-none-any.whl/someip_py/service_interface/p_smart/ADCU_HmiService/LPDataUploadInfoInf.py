from someip_py.codec import *


class NOPTime1(SomeIpPayload):

    hour: Uint16

    minute: Uint16

    def __init__(self):

        self.hour = Uint16()

        self.minute = Uint16()


class LPDataUploadInfoKls(SomeIpPayload):

    LPTimeSeN: NOPTime1

    LPDistanceSeN: Uint16

    def __init__(self):

        self.LPTimeSeN = NOPTime1()

        self.LPDistanceSeN = Uint16()


class LPDataUploadInfo(SomeIpPayload):

    LPDataUploadInfo: LPDataUploadInfoKls

    def __init__(self):

        self.LPDataUploadInfo = LPDataUploadInfoKls()
