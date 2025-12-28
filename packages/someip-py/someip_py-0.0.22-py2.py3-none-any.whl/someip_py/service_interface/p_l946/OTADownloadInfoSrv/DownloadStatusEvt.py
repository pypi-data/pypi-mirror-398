from someip_py.codec import *


class OTADownloadStatusStructKls(SomeIpPayload):

    _include_struct_len = True

    InstallationorderUUID: SomeIpDynamicSizeString

    ISOTimeStamp: SomeIpDynamicSizeString

    Newstatus: SomeIpDynamicSizeString

    Reason: SomeIpDynamicSizeString

    Downloadsize: Uint32

    def __init__(self):

        self.InstallationorderUUID = SomeIpDynamicSizeString()

        self.ISOTimeStamp = SomeIpDynamicSizeString()

        self.Newstatus = SomeIpDynamicSizeString()

        self.Reason = SomeIpDynamicSizeString()

        self.Downloadsize = Uint32()


class OTADownloadStatusStruct(SomeIpPayload):

    OTADownloadStatusStruct: OTADownloadStatusStructKls

    def __init__(self):

        self.OTADownloadStatusStruct = OTADownloadStatusStructKls()
