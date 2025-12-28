from someip_py.codec import *


class MobileDownlodStructureKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    UUID: SomeIpDynamicSizeString

    ECUAddress: SomeIpDynamicSizeString

    DownloadType: SomeIpDynamicSizeString

    EncryptionType: SomeIpDynamicSizeString

    EncryptInfo: SomeIpDynamicSizeString

    FileSize: Uint32

    URLFlag: SomeIpDynamicSizeString

    SpecifiedurlArray: SomeIpDynamicSizeArray[SomeIpDynamicSizeString]

    def __init__(self):

        self.UUID = SomeIpDynamicSizeString()

        self.ECUAddress = SomeIpDynamicSizeString()

        self.DownloadType = SomeIpDynamicSizeString()

        self.EncryptionType = SomeIpDynamicSizeString()

        self.EncryptInfo = SomeIpDynamicSizeString()

        self.FileSize = Uint32()

        self.URLFlag = SomeIpDynamicSizeString()

        self.SpecifiedurlArray = SomeIpDynamicSizeArray(SomeIpDynamicSizeString)


class MobileDownlodStructure(SomeIpPayload):

    MobileDownlodStructure: MobileDownlodStructureKls

    def __init__(self):

        self.MobileDownlodStructure = MobileDownlodStructureKls()


class OTASignatureCertificateRespStructKls(SomeIpPayload):

    _include_struct_len = True

    Status: SomeIpDynamicSizeString

    RetVal: Uint8

    def __init__(self):

        self.Status = SomeIpDynamicSizeString()

        self.RetVal = Uint8()


class OTASignatureCertificateRespStruct(SomeIpPayload):

    OTASignatureCertificateRespStruct: OTASignatureCertificateRespStructKls

    def __init__(self):

        self.OTASignatureCertificateRespStruct = OTASignatureCertificateRespStructKls()
