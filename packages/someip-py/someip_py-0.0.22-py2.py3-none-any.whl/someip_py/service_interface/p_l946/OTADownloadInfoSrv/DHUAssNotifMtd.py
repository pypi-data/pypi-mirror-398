from someip_py.codec import *


class PostInstallationInfoStructKls(SomeIpPayload):

    _include_struct_len = True

    Installationorder: SomeIpDynamicSizeString

    Isotimestamp: SomeIpDynamicSizeString

    Newstatus: SomeIpDynamicSizeString

    Reason: SomeIpDynamicSizeString

    def __init__(self):

        self.Installationorder = SomeIpDynamicSizeString()

        self.Isotimestamp = SomeIpDynamicSizeString()

        self.Newstatus = SomeIpDynamicSizeString()

        self.Reason = SomeIpDynamicSizeString()


class PostInstallationInfoStruct(SomeIpPayload):

    PostInstallationInfoStruct: PostInstallationInfoStructKls

    def __init__(self):

        self.PostInstallationInfoStruct = PostInstallationInfoStructKls()


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
