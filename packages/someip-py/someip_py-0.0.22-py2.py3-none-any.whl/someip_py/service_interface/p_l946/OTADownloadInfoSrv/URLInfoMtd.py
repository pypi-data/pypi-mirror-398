from someip_py.codec import *


class OTAURLInfoStructKls(SomeIpPayload):
    _has_dynamic_size = True
    _include_struct_len = True

    InstallationorderUUID: SomeIpDynamicSizeString

    Downloadtype: SomeIpDynamicSizeString

    Encryptiontype: SomeIpDynamicSizeString

    Encryptinfo: SomeIpDynamicSizeString

    FileSize: Uint32

    EcuAddress: SomeIpDynamicSizeString

    SpecifiedurlArray: SomeIpDynamicSizeArray[SomeIpDynamicSizeString]

    def __init__(self):

        self.InstallationorderUUID = SomeIpDynamicSizeString()

        self.Downloadtype = SomeIpDynamicSizeString()

        self.Encryptiontype = SomeIpDynamicSizeString()

        self.Encryptinfo = SomeIpDynamicSizeString()

        self.FileSize = Uint32()

        self.EcuAddress = SomeIpDynamicSizeString()

        self.SpecifiedurlArray = SomeIpDynamicSizeArray(SomeIpDynamicSizeString)


class OTAURLInfoStruct(SomeIpPayload):

    OTAURLInfoStruct: OTAURLInfoStructKls

    def __init__(self):

        self.OTAURLInfoStruct = OTAURLInfoStructKls()


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
