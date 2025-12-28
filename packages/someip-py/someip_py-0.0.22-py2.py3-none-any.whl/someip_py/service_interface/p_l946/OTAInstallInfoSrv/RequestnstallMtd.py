from someip_py.codec import *


class String(SomeIpPayload):

    String: SomeIpDynamicSizeString

    def __init__(self):

        self.String = SomeIpDynamicSizeString()


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
