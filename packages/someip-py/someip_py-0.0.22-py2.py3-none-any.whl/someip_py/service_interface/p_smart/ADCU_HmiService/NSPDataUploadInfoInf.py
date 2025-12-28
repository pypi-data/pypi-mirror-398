from someip_py.codec import *


class NOPTime1(SomeIpPayload):

    hour: Uint16

    minute: Uint16

    def __init__(self):

        self.hour = Uint16()

        self.minute = Uint16()


class NSPDataUploadInfoKls(SomeIpPayload):

    NspUsageCity: Uint16

    NspLaneChangetimes: Uint16

    NspTimeSeN: NOPTime1

    NspDistanceSeN: Uint16

    def __init__(self):

        self.NspUsageCity = Uint16()

        self.NspLaneChangetimes = Uint16()

        self.NspTimeSeN = NOPTime1()

        self.NspDistanceSeN = Uint16()


class NSPDataUploadInfo(SomeIpPayload):

    NSPDataUploadInfo: NSPDataUploadInfoKls

    def __init__(self):

        self.NSPDataUploadInfo = NSPDataUploadInfoKls()
