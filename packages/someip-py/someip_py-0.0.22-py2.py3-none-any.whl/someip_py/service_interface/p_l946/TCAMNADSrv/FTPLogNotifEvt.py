from someip_py.codec import *


class FTPLogNotifStructKls(SomeIpPayload):

    _include_struct_len = True

    LogProcess: Int16

    Filepath: SomeIpDynamicSizeString

    Filesize: Int16

    Ftpport: Int16

    Ftpuser: SomeIpDynamicSizeString

    Ftppwd: SomeIpDynamicSizeString

    def __init__(self):

        self.LogProcess = Int16()

        self.Filepath = SomeIpDynamicSizeString()

        self.Filesize = Int16()

        self.Ftpport = Int16()

        self.Ftpuser = SomeIpDynamicSizeString()

        self.Ftppwd = SomeIpDynamicSizeString()


class FTPLogNotifStruct(SomeIpPayload):

    FTPLogNotifStruct: FTPLogNotifStructKls

    def __init__(self):

        self.FTPLogNotifStruct = FTPLogNotifStructKls()
