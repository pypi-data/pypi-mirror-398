from someip_py.codec import *


class NOPTime1(SomeIpPayload):

    hour: Uint16

    minute: Uint16

    def __init__(self):

        self.hour = Uint16()

        self.minute = Uint16()


class ACCDataUploadInfoKls(SomeIpPayload):

    ACCTimeSeN: NOPTime1

    ACCDistanceSeN: Uint16

    def __init__(self):

        self.ACCTimeSeN = NOPTime1()

        self.ACCDistanceSeN = Uint16()


class ACCDataUploadInfo(SomeIpPayload):

    ACCDataUploadInfo: ACCDataUploadInfoKls

    def __init__(self):

        self.ACCDataUploadInfo = ACCDataUploadInfoKls()
