from someip_py.codec import *


class ADASHandsOffUploadInfoKls(SomeIpPayload):

    DriverHandsofftimesSeN: Uint16

    def __init__(self):

        self.DriverHandsofftimesSeN = Uint16()


class ADASHandsOffUploadInfo(SomeIpPayload):

    ADASHandsOffUploadInfo: ADASHandsOffUploadInfoKls

    def __init__(self):

        self.ADASHandsOffUploadInfo = ADASHandsOffUploadInfoKls()
