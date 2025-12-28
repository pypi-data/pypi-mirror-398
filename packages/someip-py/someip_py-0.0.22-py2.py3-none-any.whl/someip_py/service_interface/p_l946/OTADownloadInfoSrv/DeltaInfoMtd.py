from someip_py.codec import *


class SoftwarePartDeltaInfoStruct(SomeIpPayload):

    _include_struct_len = True

    FileName: SomeIpDynamicSizeString

    PartType: SomeIpDynamicSizeString

    FileSize: Uint32

    IsDelta: Uint8

    Reserve1: SomeIpDynamicSizeString

    def __init__(self):

        self.FileName = SomeIpDynamicSizeString()

        self.PartType = SomeIpDynamicSizeString()

        self.FileSize = Uint32()

        self.IsDelta = Uint8()

        self.Reserve1 = SomeIpDynamicSizeString()


class DeltaUrl(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    EcuAddress: SomeIpDynamicSizeString

    DownloadType: SomeIpDynamicSizeString

    Fileencryptiontype: SomeIpDynamicSizeString

    EncryptInfo: SomeIpDynamicSizeString

    DeltaUrlList: SomeIpDynamicSizeArray[SomeIpDynamicSizeString]

    FileSize: Uint32

    Reserve1: SomeIpDynamicSizeString

    def __init__(self):

        self.EcuAddress = SomeIpDynamicSizeString()

        self.DownloadType = SomeIpDynamicSizeString()

        self.Fileencryptiontype = SomeIpDynamicSizeString()

        self.EncryptInfo = SomeIpDynamicSizeString()

        self.DeltaUrlList = SomeIpDynamicSizeArray(SomeIpDynamicSizeString)

        self.FileSize = Uint32()

        self.Reserve1 = SomeIpDynamicSizeString()


class OTADeltaInfoStructKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    UUID: SomeIpDynamicSizeString

    Ecuaddress: SomeIpDynamicSizeString

    EnableDelta: Uint8

    DownloadStrategy: Uint32

    InstallationStrategy: Uint32

    SoftwarePartDeltaInfoArray: SomeIpDynamicSizeArray[SoftwarePartDeltaInfoStruct]

    DeltaUrls: DeltaUrl

    Reserve1: SomeIpDynamicSizeString

    Reserve2: SomeIpDynamicSizeString

    def __init__(self):

        self.UUID = SomeIpDynamicSizeString()

        self.Ecuaddress = SomeIpDynamicSizeString()

        self.EnableDelta = Uint8()

        self.DownloadStrategy = Uint32()

        self.InstallationStrategy = Uint32()

        self.SoftwarePartDeltaInfoArray = SomeIpDynamicSizeArray(
            SoftwarePartDeltaInfoStruct
        )

        self.DeltaUrls = DeltaUrl()

        self.Reserve1 = SomeIpDynamicSizeString()

        self.Reserve2 = SomeIpDynamicSizeString()


class OTADeltaInfoStruct(SomeIpPayload):

    OTADeltaInfoStruct: OTADeltaInfoStructKls

    def __init__(self):

        self.OTADeltaInfoStruct = OTADeltaInfoStructKls()


class OTADeltaInfoRespStructKls(SomeIpPayload):

    _include_struct_len = True

    Status: SomeIpDynamicSizeString

    Retval: Uint8

    def __init__(self):

        self.Status = SomeIpDynamicSizeString()

        self.Retval = Uint8()


class OTADeltaInfoRespStruct(SomeIpPayload):

    OTADeltaInfoRespStruct: OTADeltaInfoRespStructKls

    def __init__(self):

        self.OTADeltaInfoRespStruct = OTADeltaInfoRespStructKls()
